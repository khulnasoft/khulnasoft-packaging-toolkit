# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from collections import (
    Iterable,
    Mapping,
    MutableMapping,
    OrderedDict,
    ItemsView,
    KeysView,
    ValuesView,
    Set,
)  # pylint: disable=no-name-in-module
from json import JSONDecoder, JSONEncoder

import io
import sys

from semantic_version import Version
import semantic_version

from ...utils.internal import long  # pylint: disable=redefined-builtin
from ...utils import SlimLogger, string, typing
from .json_data import JsonSchema

if typing is not None:
    Tuple = typing.Tuple
    Union = typing.Union


class ObjectView(MutableMapping):
    """Presents a JSON-serializable object view over an :class:`OrderedDict`.

    Derived classes should add slots to support instance variables that shouldn't be serialized from self.__dict__.
    Consumers should use :meth:`ObjectView.viewitems`, :meth:`ObjectView.viewkeys`, and :meth:`ObjectView.viewvalues`
    to iterate over elements of the `OrderedDict` underlying instances of this class.

    """

    # On Python 2.7 the abstract base collection classes are old-style. This means that self.__dict__ is defined even
    # when slots are defined. Python 3.x works differently. If you want self.__dict__, you must ask for it.

    __slots__ = () if sys.version_info.major == 2 else ("__dict__",)

    def __init__(self, value, onerror=None):
        # type: (Union[typing.Iterable[Tuple[string, object]], ObjectView, string]) -> None

        schema = getattr(type(self), "schema", None)

        if onerror is None:
            onerror = SlimLogger.error

        if isinstance(value, string):

            try:
                value = ObjectView._decode(value)
            except ValueError as error:
                if schema is None:
                    message = "Poorly formed " + "JSON: " + value
                else:
                    message = schema.name + ": " + string(error) + ": " + value
                onerror(message)
                return

            if not isinstance(value, ObjectView):
                onerror(
                    "Expected a JSON object, not "
                    + ObjectView.get_json_type_name(value)
                    + ": "
                    + value
                )
                return

            attributes = value.__dict__

        elif isinstance(value, ObjectView):
            attributes = value.__dict__

        elif isinstance(value, Iterable):
            attributes = OrderedDict(
                (k, ObjectView(v) if isinstance(v, Mapping) else v) for k, v in value
            )

        else:
            raise TypeError(
                "Invalid argument: expected a string, Mapping, or Iterable instance; not "
                + value.__class__.__name__
                + ": "
                + string(value)
            )

        self.__dict__ = (
            schema.convert_from(attributes, onerror)
            if isinstance(schema, JsonSchema)
            else attributes
        )

    # region Special methods

    def __repr__(self):
        return self.__class__.__name__ + "(" + self.__str__() + ")"

    def __str__(self):
        return ObjectView.encode(self)

    # region ... MutableMapping interface

    def __delitem__(self, name):
        self.__dict__.__delitem__(name)

    def __getitem__(self, name):
        return self.__dict__.__getitem__(name)

    def __contains__(self, name):
        return self.__dict__.__contains__(name)

    def __iter__(self):
        return self.__dict__.__iter__()

    def __len__(self):
        return self.__dict__.__len__()

    def __setitem__(self, name, value):
        self.__dict__.__setitem__(name, value)

    # endregion

    # endregion

    # region Properties

    empty = None

    # endregion

    # region Methods

    @staticmethod
    def dumps(value):
        return ObjectView.encode(value)

    @staticmethod
    def get_json_type_name(value):
        value_type = value if not isinstance(value, type) else type(value)
        return ObjectView._json_type_map.get(value_type, "unknown")

    # pylint: disable=redefined-builtin
    def save(self, file, indent=False):
        if isinstance(file, string):
            with io.open(file, encoding="utf-8", mode="w", newline="") as ostream:
                self._save(ostream, indent)
            return
        self._save(file, indent)

    @staticmethod
    def to_dict_helper(items=None):
        return ObjectView._to_dict(items)

    def to_dict(self, items=None):
        # type: () -> dict
        if items is None:  # pylint: disable=no-else-return
            return self._to_dict(self.viewitems())
        else:
            return self._to_dict(items)

    def viewitems(self):
        # type: () -> ItemsView
        return ItemsView(self)

    def viewkeys(self):
        # type: () -> KeysView
        return KeysView(self)

    def viewvalues(self):
        # type: () -> ValuesView
        return ValuesView(self)

    # endregion

    # region Protected

    # These fields cannot be properly initialized until current class is defined
    _json_type_map = None

    @staticmethod
    def _create_object_view(pairs):
        return ObjectView(pairs)

    # noinspection PyUnresolvedReferences
    _decode = JSONDecoder(object_pairs_hook=_create_object_view.__func__).decode

    @staticmethod
    def _default(element):

        if isinstance(element, ObjectView):
            # pylint: disable=protected-access
            return None if element is ObjectView.empty else element.__dict__

        try:
            return element.to_dict()
        except AttributeError:
            pass

        if isinstance(element, (semantic_version.Spec, Version)):
            return string(element)

        if isinstance(element, Mapping):
            return OrderedDict(element.items())

        if isinstance(element, Iterable):
            return list(
                element
            )  # Supports Set--which the json module will not encode--as well as list and tuple

        raise TypeError()

    # noinspection PyUnresolvedReferences
    encode = JSONEncoder(default=_default.__func__, ensure_ascii=False).encode

    # noinspection PyUnresolvedReferences
    iterencode = JSONEncoder(
        default=_default.__func__, separators=(",", ":")
    ).iterencode

    # noinspection PyUnresolvedReferences
    iterencode_indent = JSONEncoder(default=_default.__func__, indent=2).iterencode

    def _save(self, ostream, indent):
        iterencode = (
            ObjectView.iterencode_indent if indent is True else ObjectView.iterencode
        )
        for chunk in iterencode(self):
            if sys.version_info >= (3, 0):
                if hasattr(ostream, "encoding"):
                    # ostream is text
                    chunk = string(chunk)
                else:
                    # ostream is binary
                    chunk = string(chunk).encode()
            else:
                # hasattr(ostream, 'encoding') evalutes true either way for
                # binary or text streams on py2
                chunk = string(chunk)
            ostream.write(chunk)

    @classmethod
    def _to_dict(cls, items):
        # type: (typing.Iterable[typing.Tuple[string, object]]) -> dict
        def convert(item):
            if isinstance(item, (bool, int, long, float, string, type(None))):
                return item
            if isinstance(item, Mapping):
                return dict(((n, convert(v)) for n, v in item.items()))
            if isinstance(item, (list, Set)):
                return list((convert(v) for v in item))
            if hasattr(item, "to_dict"):
                return item.to_dict()
            return string(item)

        return {name: convert(value) for name, value in items}

    def _validate_field_names(
        self, view_name, all_field_names, opt_field_names=tuple()
    ):

        # Check if view has all possible field names defined
        difference = all_field_names.symmetric_difference(self.__dict__)
        if len(difference) == 0:
            return

        # Verify remaining fields are declared optional
        if len(difference.difference(opt_field_names)) == 0:
            return

        # Required fields not defined, or unknown fields defined
        raise ValueError(
            "Invalid " + view_name + " (missing/unknown fields): " + string(self)
        )

    # endregion
    pass  # pylint: disable=unnecessary-pass


# We can't initialize these two fields until the ObjectView class is fully defined and so we define them here rather
# than in a lazy-fashion in ObjectView.get_json_type_name

ObjectView._json_type_map = {  # pylint: disable=protected-access
    ObjectView: "object",
    frozenset: "array",
    list: "array",
    string: "string",
    int: "number",
    long: "number",
    float: "number",
    bool: "boolean",
    type(None): "null",
    Version: "string",
    semantic_version.Spec: "string",
}

ObjectView.empty = ObjectView(())
