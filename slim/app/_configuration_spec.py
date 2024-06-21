# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

""" app_configuration_spec module

The app_configuration_spec module defines this class hierarchy:

.. code-block::
    AppConfigurationSpec(NamedObject)
    |
    └-> stanzas: (name: string, AppConfigurationStanzaDeclaration(NamedObject))*
                                |
                                ├-> pattern: SRE_Pattern
                                |
                                ├-> documentation: AppConfigurationDocumentation*
                                |
                                ├-> placement: AppConfigurationPlacement
                                |
                                ├-> position: FilePosition
                                |
                                └-> settings: (name: string, AppConfigurationSettingDeclaration(NamedObject)*
                                                             |
                                                             ├-> pattern: SRE_Pattern
                                                             |
                                                             ├-> data_type: string
                                                             |
                                                             ├-> position: FilePosition
                                                             |
                                                             ├-> documentation: AppConfigurationDocumentation*
                                                             |
                                                             └-> placement: AppConfigurationPlacement
                                                                            |
                                                                            ├-> forwarder: Boolean
                                                                            |
                                                                            ├-> indexer: Boolean
                                                                            |
                                                                            ├-> search_head: Boolean
                                                                            |
                                                                            └-> workloads: tuple(string{1,3})

"""

from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import object
from collections import OrderedDict
from os import path

import re
import sys

from keyword import iskeyword

from ._configuration_validation_plugin import AppConfigurationValidationPlugin
from ._internal import FileBuffer, NamedObject
from ..utils import SlimLogger, encode_string, escape_non_alphanumeric_chars
from ..utils.internal import string


class AppConfigurationDocumentation(object):
    def __init__(
        self, text, bulleted, indentation, line_spacing, position
    ):  # pylint: disable=too-many-arguments

        self._text = text
        self._bulleted = bulleted
        self._indentation = indentation
        self._line_spacing = line_spacing

        self._position = position

    def __str__(self):
        spaces = " " * self._indentation
        newlines = "\n" * self._line_spacing
        return (
            (spaces + "* " + self._text + newlines)
            if self._bulleted
            else (spaces + self._text + newlines)
        )

    @property
    def position(self):
        return self._position

    @property
    def text(self):
        return self._text


class AppConfigurationPlacement(object):

    __slots__ = ("_workloads",)

    def __new__(cls, workloads):

        try:
            workloads = cls._normalize_workloads(workloads)
        except KeyError:
            raise ValueError(
                "Unrecognized placement: "
                + ", ".join((string(workload) for workload in workloads))
            )

        instance = cls._workloads_set[workloads]
        if instance is not None:
            return instance
        if sys.version_info < (3, 0):
            return super(AppConfigurationPlacement, cls).__new__(cls, workloads)
        return super(AppConfigurationPlacement, cls).__new__(cls)

    def __init__(self, workloads):
        self._workloads = AppConfigurationPlacement._normalize_workloads(workloads)
        AppConfigurationPlacement._workloads_set[self._workloads] = self

    # region Special methods

    def __repr__(self):
        return repr(self._workloads)

    def __str__(self):
        return "@placement " + ", ".join(self._workloads)

    # endregion

    # region Properties

    all_workloads = None

    @property
    def forwarder(self):
        return "forwarder" in self._workloads

    @property
    def indexer(self):
        return "indexer" in self._workloads

    @property
    def search_head(self):
        return "search-head" in self._workloads

    @property
    def workloads(self):
        return self._workloads

    # endregion

    # region Methods

    def is_disjoint(self, other):
        return not self.is_overlapping(other)

    def is_overlapping(self, other):
        if not isinstance(other, AppConfigurationPlacement):
            other = AppConfigurationPlacement(other)
        workloads = self.workloads
        return any((workload in workloads for workload in other.workloads))

    def to_dict(self):
        names = self._serialization_names
        return OrderedDict(
            (
                (names[v], getattr(self, v))
                for v in ("forwarder", "indexer", "search_head")
            )
        )

    def union(self, other):
        if other is None:
            return self
        # noinspection PyProtectedMember
        return AppConfigurationPlacement(
            other._workloads + self._workloads
        )  # pylint: disable=protected-access

    # endregion

    # region Protected

    @classmethod
    def _normalize_workloads(cls, item):
        return tuple(
            sorted(
                (cls._synonymous_names[name] for name in frozenset(item)), reverse=True
            )
        )

    _serialization_names = {
        "search_head": "searchHead",
        "forwarder": "forwarder",
        "indexer": "indexer",
    }

    _synonymous_names = {
        "search-head": "search-head",
        "search_head": "search-head",
        "searchHead": "search-head",
        "forwarder": "forwarder",
        "indexer": "indexer",
    }

    _workloads_set = OrderedDict(
        [
            (("search-head",), None),
            (("forwarder",), None),
            (("indexer",), None),
            (("indexer", "forwarder"), None),
            (("search-head", "indexer"), None),
            (("search-head", "forwarder"), None),
            (("search-head", "indexer", "forwarder"), None),
        ]
    )

    # endregion


AppConfigurationPlacement.all_workloads = AppConfigurationPlacement(
    ("search-head", "indexer", "forwarder")
)


class AppConfigurationSettingDeclaration(NamedObject):
    def __init__(self, name):
        NamedObject.__init__(self, name)
        self._sections = OrderedDict()
        self._declaration = None

    # region Special methods

    def __repr__(self):
        arguments = (
            "name=" + repr(self._name),
            "data_type=" + repr(self.data_type),
            "placement=" + repr(self.placement),
            "position=" + repr(self.position),
        )
        return "AppConfigurationSetting(" + ", ".join(arguments) + ")"

    def __str__(self):
        return self._declaration.__str__()

    # endregion

    # region Properties

    @property
    def data_type(self):
        return self._declaration.data_type

    @property
    def documentation(self):
        return self._declaration.documentation

    @property
    def pattern(self):
        return self._declaration.pattern

    @property
    def placement(self):
        return self._declaration.placement

    @property
    def position(self):
        return self._declaration.position

    # endregion

    # region Methods

    def add(self, section):
        self._sections[section.name] = self._declaration = section

    # endregion

    class Section(NamedObject):
        def __init__(self, name, data_type, placement, position):

            NamedObject.__init__(self, name)

            self._data_type = data_type
            self._placement = placement
            self._position = position
            self._documentation = []

            self._pattern = self._compile_pattern(name)

        # region Special methods

        def __repr__(self):
            arguments = (
                "name=" + repr(self._name),
                "data_type=" + repr(self._data_type),
                "placement=" + repr(self._placement),
                "position=" + repr(self._position),
            )
            return "AppConfigurationSetting.Section(" + ", ".join(arguments) + ")"

        def __str__(self):
            return self._name + " = " + self._data_type

        # endregion

        # region Properties

        @property
        def data_type(self):
            return self._data_type

        @property
        def documentation(self):
            return self._documentation

        @property
        def pattern(self):
            return self._pattern

        @property
        def placement(self):
            return self._placement

        @property
        def position(self):
            return self._position

        # endregion

        # region Protected

        # TODO: Refactor AppConfiguration{SettingDeclaration,StanzaDeclaration}._compile_pattern into shared/unique code
        # Difference: stanza name patterns are a bit more complex on the _sub_replacement_pattern side and therefore
        # have different replace(match) functions

        def _compile_pattern(self, name):
            def replace(match):
                group_name = to_valid_identifier(
                    match.expand(match.group(1)), match.start(1)
                )
                return r"(?P<" + group_name + ">.*?)"

            def to_valid_identifier(group_name, start):
                if len(group_name) == 0:
                    group_name = "__unnamed_group_" + string(start)
                else:
                    group_name = self._sub_invalid_identifier_characters(
                        "_", group_name
                    )
                    if group_name[0].isdigit() or iskeyword(group_name):
                        group_name = "_" + group_name
                return group_name

            # guards against compilation of embedded regular expressions
            escaped_text = escape_non_alphanumeric_chars(name)
            try:
                pattern = re.compile(
                    self._sub_replacement_pattern(replace, escaped_text) + r"\Z",
                    re.M | re.U,
                )
                return pattern
            except re.error as error:
                SlimLogger.fatal(
                    self.position,
                    ": Could not compile regular expression for stanza header [",
                    name,
                    "]: ",
                    error,
                )

        # TODO: Ensure optional match strings in stanza names are consistent with SpecFiles.cpp
        # Is there just the one use case for optional matches: inputs.conf.spec?

        _sub_invalid_identifier_characters = re.compile(
            r"\\[_\W](?<!\\\\)|(?=\w)[^a-zA-Z0-9]", re.M | re.U
        ).sub
        _sub_replacement_pattern = re.compile(r"\\<(.*?)\\>", re.M | re.U).sub

        # endregion
        pass  # pylint: disable=unnecessary-pass


class AppConfigurationSpec(NamedObject):
    def __init__(self, name, app_root):
        NamedObject.__init__(self, name)
        self._app_root = app_root
        self._sections = OrderedDict()
        self._declarations = OrderedDict()
        self._validation_plugin = AppConfigurationValidationPlugin.get(name, app_root)

    # region Special methods

    def __repr__(self):
        return (
            "AppConfigurationSpec(name="
            + repr(self._name)
            + "stanzas="
            + repr(self._declarations)
            + ")"
        )

    def __str__(self):
        return encode_string(self._name)

    # endregion

    # region Methods

    def load(self, filename):

        section = AppConfigurationSpec.Section.load(filename, self._validation_plugin)
        section_declarations = section.stanza_declarations
        declarations = self._declarations

        for name in section_declarations:
            section_declaration = section_declarations[name]
            try:
                declaration = declarations[name]
            except KeyError:
                declaration = AppConfigurationStanzaDeclaration(
                    name, section_declaration.position
                )
                declarations[name] = declaration
            declaration.add(section_declaration)

        self._sections[filename] = section

    def match(self, stanza):
        declarations = self._declarations
        matches = []

        for name in self._declarations:
            declaration = declarations[name]
            match = declaration.pattern.match(stanza)
            if match is not None:
                matches.append(declaration)

        return matches if len(matches) > 0 else None

    def stanza_declarations(self):
        declarations = self._declarations
        return (declarations[name] for name in declarations)

    def to_dict(self):
        copies = self._sections
        return OrderedDict(
            ((name, copies[name]) for name in self._sections)
        )  # we copy to protect our internals

    # endregion

    class Section(NamedObject):
        def __init__(self, file_buffer):
            name = path.basename(file_buffer.filename)
            if name.endswith(".conf.spec"):
                end = len(".conf.spec")
                if end < len(name):
                    name = name[:end]
            NamedObject.__init__(self, name)
            self._buffer = file_buffer

        # region Properties

        @property
        def filename(self):
            return self._buffer.filename

        def get(self, stanza):
            return self._buffer.stanza_declarations[stanza]

        @classmethod
        def load(cls, filename, validation_plugin):
            file_buffer = _AppConfigurationSpecBuffer(filename, validation_plugin)
            file_buffer.load()
            return cls(file_buffer)

        @property
        def stanza_declarations(self):
            return self._buffer.stanza_declarations

        # endregion

        # region Methods

        def save(self, filename=None):
            self._buffer.save(filename)

        # endregion
        pass  # pylint: disable=unnecessary-pass


class AppConfigurationStanzaDeclaration(NamedObject):
    def __init__(self, name, position):
        NamedObject.__init__(self, name)
        self._placement = None
        self._sections = OrderedDict()
        self._declarations = OrderedDict()
        self._patterned_declarations = None
        self._pattern = self._compile_pattern(name, position)

    # region Special methods

    def __repr__(self):
        name, declarations = repr(self._name), repr(self._declarations)
        return (
            "AppConfigurationStanzaDeclaration(name="
            + name
            + ", setting_declarations="
            + declarations
            + ")"
        )

    def __str__(self):
        return "[" + self._name.replace("\n", "\\n") + "]"

    # endregion

    # region Properties

    @property
    def pattern(self):
        return self._pattern

    @property
    def placement(self):
        return self._placement

    # endregion

    # region Methods

    def add(self, section):

        section_declarations = section.setting_declarations
        declarations = self._declarations

        for name in section_declarations:
            try:
                declaration = declarations[name]
            except KeyError:
                declaration = AppConfigurationSettingDeclaration(name)
                declarations[name] = declaration
            declaration.add(section_declarations[name])

        self._sections[section.position.file] = section
        self._placement = section.placement.union(self._placement)

    def match(self, setting):

        # match exact

        declarations = self._declarations
        name = setting.name

        try:
            return declarations[name]
        except KeyError:
            pass

        # match pattern

        declarations = self._patterned_declarations

        if declarations is None:
            declarations = [
                d for d in list(self._declarations.values()) if d.name != d.pattern
            ]
            self._patterned_declarations = declarations

        for declaration in declarations:
            match = declaration.pattern.match(name)
            if match is None:
                continue
            return declaration

        return None

    def setting_declarations(self):
        declarations = self._declarations
        return (declarations[name] for name in declarations)

    # endregion

    # region Protected

    def _compile_pattern(self, name, position):
        def replace(match):
            group_name = to_valid_identifier(
                match.expand(match.group(2)), match.start(2)
            )
            prefix = match.group(1)
            suffix = match.group(3)
            if len(prefix) > 0 and len(suffix) > 0:
                # Match zero or one occurrence of arbitrary text with a symbolic `group` name
                # The text must be followed by a colon (':'), if the pattern `suffix` is ':'
                sub_pattern = r"(?P<" + group_name + ">.*?" + suffix[2:] + ")?"
            else:
                # Match one occurrence of arbitrary text with a symbolic `group` name
                sub_pattern = r"(?P<" + group_name + ">.*?)"
            return sub_pattern

        def to_valid_identifier(group_name, start):
            if len(group_name) == 0:
                group_name = "__unnamed_group_" + string(start)
            else:
                group_name = self._sub_invalid_identifier_characters("_", group_name)
                if group_name[0].isdigit() or iskeyword(group_name):
                    group_name = "_" + group_name
                if group_name in group_names:
                    group_name += "_" + string(start)
                group_names.add(group_name)
            return group_name

        names = name.split("|")
        group_names = set()

        for index, text in enumerate(names):
            scheme = self._match_scheme_name(text)
            if scheme is not None:
                text = text[scheme.end() :]
            # guards against compilation of embedded regular expressions
            escaped_text = escape_non_alphanumeric_chars(text)
            pattern = self._sub_replacement_pattern(replace, escaped_text)
            if scheme is None:
                names[index] = pattern
                continue
            names[index] = scheme.group(1) + "|" + scheme.group(0) + pattern

        pattern = (
            "(?:" + "|".join(names) + ")\\Z" if len(names) > 1 else names[0] + "\\Z"
        )

        try:
            pattern = re.compile(pattern, re.M | re.U)
            return pattern
        except re.error as error:
            SlimLogger.fatal(
                position,
                ": Could not compile regular expression for stanza header [",
                name,
                "]: ",
                error,
            )

    _match_scheme_name = re.compile(
        r"([0-9a-zA-Z][0-9a-zA-Z_-]*)://", re.M | re.U
    ).match
    _sub_invalid_identifier_characters = re.compile(
        r"\\[_\W](?<!\\\\)|(?=\w)[^a-zA-Z0-9]", re.M | re.U
    ).sub
    _sub_replacement_pattern = re.compile(
        r"((?:\\\[)?)\\<(.*?)\\>((?:\\\]\\:)?)", re.M | re.U
    ).sub

    # endregion

    class Section(NamedObject):
        def __init__(self, name, position):

            NamedObject.__init__(self, name)
            self._declarations = OrderedDict()
            self._documentation = []
            self._placement = None
            self._position = position

        # region Special methods

        def __repr__(self):
            name, position = repr(self._name), repr(self._position)
            return (
                "AppConfigurationStanzaDeclaration.Section(name="
                + name
                + "position="
                + position
                + ")"
            )

        def __str__(self):
            return "[" + self._name.replace("\n", "\\n") + "]"

        # endregion

        # region Properties

        @property
        def documentation(self):
            return self._documentation

        @property
        def placement(self):
            return self._placement

        @property
        def position(self):
            return self._position

        @property
        def setting_declarations(self):
            return self._declarations

        # endregion


class _AppConfigurationSpecBuffer(FileBuffer):
    def __init__(self, filename, validation_plugin):
        FileBuffer.__init__(self, filename)
        self._stanza_declarations = None
        self._validation_plugin = validation_plugin

    # region Properties

    @property
    def stanza_declarations(self):
        return self._stanza_declarations

    # endregion

    # region Protected

    _any_stanza_name = "<__any_stanza_name>"

    _is_bulleted_paragraph = re.compile(r"\*\s", re.M | re.U).match
    _match_any_stanza_name = re.compile(r"<[^<>]+>", re.M | re.U).match
    _match_placement_directive = re.compile(r"@\s*placement\s+", re.M | re.U).match
    _search_last_whitespace = re.compile(r"\s*$", re.MULTILINE).search
    _split_comma_delimited_text = re.compile(r"\s*, \s*", re.M | re.U).split

    # pylint: disable=protected-access
    def _load(self, reader, **kwargs):
        """Reads the conf.spec file associated with the current Buffer"""
        # TODO: SPL-123949: Refactor AppConfigurationSpecBuffer._load to improve understandability
        # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        stanza = AppConfigurationStanzaDeclaration.Section("default", reader.position)
        setting_declaration_section = AppConfigurationSettingDeclaration.Section
        stanzas = self._stanza_declarations = OrderedDict()
        stanzas["default"] = current_item = stanza
        aggregate_placement = default_placement = placement = None

        match_assignment_statement = self._match_assignment_statement
        skip_whitespace = self._skip_whitespace

        for line in reader:  # pylint: disable=too-many-nested-blocks
            try:
                match = skip_whitespace(line)
                start = match.end()
                if start >= len(line):
                    # blank line
                    item = "\n"
                    start = 0
                elif line[start] in ";#":
                    # comment
                    item = line[start:]
                elif line[start] == "@":
                    # directive
                    item = self._parse_directive(line, start)
                    if default_placement is None:
                        # We're in the global settings section (i.e., outside of any stanza declaration) and this
                        # placement directive appears before the first setting declaration
                        assert (
                            stanza.name == "default"
                            and len(stanza.setting_declarations) == 0
                        )
                        default_placement = item
                    placement = item
                    aggregate_placement = placement.union(aggregate_placement)
                else:
                    line = reader.read_continuation(line)
                    if start == 0 and line[start] == "[":
                        # stanza declaration
                        item = self._parse_stanza_declaration(
                            line, start, reader, stanzas
                        )
                        if default_placement is None:
                            # We're exiting the global settings section (i.e., entering the first stanza) without
                            # having encountered a placement directive or a setting declaration
                            default_placement = AppConfigurationPlacement.all_workloads
                        self._end_stanza_declaration(
                            stanza,
                            aggregate_placement,
                            default_placement,
                            reader.position,
                        )
                        placement = aggregate_placement = item.placement
                        current_item = stanza = item
                    else:
                        match = match_assignment_statement(line, start)
                        if match is None:
                            # documentation for the current item which is either a stanza or a setting declaration
                            item = self._parse_documentation(line, start, reader)
                            current_item.documentation.append(item)
                        else:
                            # setting declaration
                            if default_placement is None:
                                # We're in the global settings section (i.e., outside of any stanza declaration) and
                                # this setting declaration appears before the first, if any placement directive
                                assert (
                                    stanza.name == "default"
                                    and len(stanza.setting_declarations) == 0
                                )
                                default_placement = (
                                    AppConfigurationPlacement.all_workloads
                                )
                            if aggregate_placement is None:
                                # We're in the global settings section or some stanza declaration (the default or some
                                # other stanza) and we've hit this setting before hitting a placement directive
                                assert placement is None
                                placement = aggregate_placement = default_placement
                            name, data_type, position = (
                                match.group(1),
                                match.group(2),
                                reader.position,
                            )
                            item = setting_declaration_section(
                                name, data_type[:-1], placement, position
                            )
                            stanza.setting_declarations[item.name] = current_item = item
                self._append(item, reader.position, indentation=start)
            except self._Error as error:
                SlimLogger.error(reader.position, ": ", error)

        if default_placement is None:
            # We're exiting the global settings section because we hit the end of the current spec file without having
            # encountered a placement directive or setting declaration. In short, we have a spec file without any
            # placement directives or setting declarations
            assert (
                stanza.name == "default"
                and len(stanza.setting_declarations) == 0
                and aggregate_placement is None
            )
            stanza._placement = (
                aggregate_placement
            ) = default_placement = AppConfigurationPlacement.all_workloads

        self._end_stanza_declaration(
            stanza, aggregate_placement, default_placement, reader.position
        )

        if len(stanzas) == 1:
            # The default stanza is the only stanza, hence all settings are global and there are no restrictions or
            # special handling based on stanza name (we'll match any stanza name)
            stanza = AppConfigurationStanzaDeclaration.Section(
                self._any_stanza_name, reader.position
            )
            stanzas[stanza.name] = stanza
            self._end_stanza_declaration(
                stanza, default_placement, default_placement, reader.position
            )
            return

        self._fix_up(reader.position)

    # pylint: disable=protected-access
    def _end_stanza_declaration(
        self, item, aggregate_placement, default_placement, position
    ):

        if item.name == "default" and len(item.setting_declarations) == 0:
            # There are no global settings so we don't add a disabled setting because it doesn't influence the placement
            # of settings for any specific stanza
            return

        placement = item._placement = (
            default_placement if aggregate_placement is None else aggregate_placement
        )
        self._validation_plugin.fix_up(item, placement, position)

    def _fix_up(self, position):

        # TODO: Incorporate this issue into module-level documentation
        # Issue:
        # * any setting can go into the default stanza, including the disabled setting
        # * the disabled setting will be found in a specific stanza, not the default stanza
        # * it is that stanza's disabled setting placement that will determine the placement of the disabled setting
        #   in the default stanza
        # * however, it is the union of all placements for all stanzas that should determine the placement of the
        #   disabled setting in the default stanza
        # Approach:
        # keep this info in the default stanza and make sure we search from a specific stanza to the default
        # stanza to match a specific stanza's setting. Search in the reverse order when matching a global setting.

        stanzas = self.stanza_declarations
        default_stanza = stanzas["default"]

        try:
            default_disabled = default_stanza.setting_declarations["disabled"]
        except KeyError:
            default_disabled = AppConfigurationSettingDeclaration.Section(
                "disabled", "<bool>", None, position
            )
            default_stanza.setting_declarations["disabled"] = default_disabled

        default_disabled_placement = aggregate_placement = default_disabled.placement

        for name in stanzas:
            if name == "default":
                continue
            stanza = stanzas[name]
            disabled = stanza.setting_declarations["disabled"]
            disabled._placement = disabled.placement.union(default_disabled_placement)
            aggregate_placement = disabled.placement.union(aggregate_placement)

        default_stanza._placement = default_disabled._placement = aggregate_placement

    def _parse_directive(self, line, start):

        match = self._match_placement_directive(line, start)

        if match is None:
            raise self._Error("expected placement directive, not " + line[start:])

        start = match.end()
        end = self._search_last_whitespace(line, start).start()
        workloads = self._split_comma_delimited_text(line[start:end])

        try:
            return AppConfigurationPlacement(workloads)
        except ValueError:
            raise self._Error(
                "Unrecognized workload in placement directive: " + ", ".join(workloads)
            )

    def _parse_documentation(self, line, start, reader):

        bulleted = self._is_bulleted_paragraph(line[start : start + 2]) is not None
        indentation = start
        line_spacing = 0
        position = reader.position

        if bulleted:
            start += 2

        paragraph = line[start:].rstrip("\n")

        for linep in reader:
            linepp, line_spacing, start = self._read_blank(linep, reader)
            if line_spacing > 0 or (len(linepp) > 0 and linepp[start] in "[@#;*"):
                # We've hit a blank line or a new record (stanza, directive, comment, or documentation)
                if len(linepp) > 0:
                    reader.put_back(linepp)
                break
            if len(linepp) > 0:
                paragraph += "\n" + linepp.rstrip("\n")

        item = AppConfigurationDocumentation(
            paragraph, bulleted, indentation, line_spacing, position
        )
        return item

    def _parse_stanza_declaration(self, line, start, reader, stanzas):

        # TODO: insist that stanzas start in column 1 because spec file authors have a habit of using stanza headers
        # in examples. See, for instance, distsearch.conf.spec, at or about line 336: "  [bundleEnforcerBlacklist]."

        start += 1
        match = self._search_right_square_bracket(line, start)

        if match is None:
            SlimLogger.warning(
                reader.position,
                ": missing terminating right square bracket at end of stanza header",
            )
            end = -1
        else:
            end = match.start()

        name = line[start:end]

        if self._match_any_stanza_name(name):
            name = self._any_stanza_name

        try:
            declaration = stanzas[name]
        except KeyError:
            declaration = AppConfigurationStanzaDeclaration.Section(
                name, reader.position
            )
            stanzas[name] = declaration

        return declaration

    def _read_blank(self, line, reader):
        """Reads to the first non-blank line, if the current line is blank

        :param line: current line
        :type line: string

        :param reader: used to read subsequent lines, if the current line is blank.
        :type reader: FileReader

        :return: (`line`, `count` `start`) where:
        `line` is the first non-blank line read or the current line, if the current line is blank. An empty string
        value indicates that EOF was encountered.
        `count` is the number of blank lines read. The current line is included in the `count`.
        `start` is the index of the first non-blank character on `line`
        :rtype: tuple

        """
        skip_whitespace = self._skip_whitespace
        start = None
        count = 0
        while True:
            match = skip_whitespace(self.line_to_unicode(line))
            start = match.end()
            if start < len(line):  # non-blank line
                break
            count += 1
            try:
                line = next(reader)
            except StopIteration:
                start = 0
                line = ""
                break
        return line, count, start

    # endregion
    pass  # pylint: disable=unnecessary-pass

    # convert NoneType to unicode, part of next() fix. SPL-168604
    def line_to_unicode(self, line):
        if line is None:
            line = ""
        return line
