# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import object
from collections import Mapping  # pylint: disable=no-name-in-module

import io
import json

from io import StringIO

from os import path
import os

import re
import sys

from semantic_version import Version

from ._internal import ObjectView
from ._internal import JsonSchema
from ._internal import JsonField, JsonValue
from ._internal import JsonArray, JsonObject, JsonString, JsonBoolean
from ._internal import (
    JsonDataTypeConverter,
    JsonFilenameConverter,
    JsonVersionConverter,
    JsonVersionSpecConverter,
)

from ..utils import (
    SlimLogger,
    encode_filename,
    encode_string,
    slim_configuration,
    string,
    typing,
)
from ..utils.public import SlimTargetOS, SlimTargetOSWildcard

if typing is not None:
    TextIO = typing.TextIO


class AppCommonInformationModelInfo(object):
    def __init__(self, iterable):
        for name, versions in iterable:
            setattr(self, name, tuple(versions))

    # We include this pylint directive because file is recognized as a built-in even though the standard Python library
    # and we commonly use file as an argument name
    # pylint: disable=redefined-builtin
    @classmethod
    def load(cls, file=None):
        if file is None:
            file = path.join(
                slim_configuration.system_config, "common-information-models.json"
            )
        if isinstance(file, string):
            with io.open(file, encoding="utf-8") as filep:
                return cls._load(filep)
        return cls._load(file)

    # region Protected

    @classmethod
    def _load(cls, istream):
        return cls.schema.convert_from(json.load(istream), onerror=SlimLogger.error)

    # endregion

    class Converter(JsonDataTypeConverter):
        def convert_from(self, data_type, value):
            assert isinstance(data_type, JsonObject) and isinstance(value, Mapping)
            return AppCommonInformationModelInfo((name, value[name]) for name in value)

        def convert_to(self, data_type, value):
            raise NotImplementedError()

    schema = JsonSchema(
        "Common information model info",
        JsonValue(
            JsonObject(
                any=JsonValue(
                    JsonArray(JsonValue(JsonString(), converter=JsonVersionConverter()))
                )
            ),
            converter=Converter(),
        ),
    )


class AppCommonInformationModelSpec(ObjectView):
    def __str__(self):
        return ", ".join((name + string(self[name]) for name in self))

    class Converter(JsonDataTypeConverter):
        def __init__(self):
            if self._info is None:
                self._info = AppCommonInformationModelInfo.load()

        def convert_from(self, data_type, value):
            assert isinstance(data_type, JsonObject) and isinstance(value, Mapping)

            def convert(name, version_spec):
                try:
                    versions = getattr(self._info, name)
                except AttributeError:
                    raise ValueError(
                        "Expected a common information model name, not "
                        + encode_string(name)
                    )
                if version_spec is None:
                    return name, None
                for version in versions:
                    if version in version_spec:
                        return name, version_spec
                raise ValueError(
                    "Version requirement includes no supported version of Khulnasoft "
                    + name
                    + ": "
                    + string(version_spec)
                )

            return AppCommonInformationModelInfo(
                (convert(name, value[name]) for name in value)
            )

        def convert_to(self, data_type, value):
            raise NotImplementedError()

        _info = None


class AppDependency(ObjectView):
    class Converter(JsonDataTypeConverter):
        def convert_from(self, data_type, value):
            assert isinstance(data_type, JsonObject) and isinstance(value, Mapping)
            return AppDependency(((name, value[name]) for name in value))

        def convert_to(self, data_type, value):
            raise NotImplementedError()


class AppDependencyPackageConverter(JsonDataTypeConverter):
    def convert_from(self, data_type, value):
        assert isinstance(data_type, JsonString) and isinstance(
            value, string
        )  # pylint: disable=unidiomatic-typecheck
        filename = os.path.basename(value)
        if value != filename:
            raise ValueError("Expected a filename, not a path: " + encode_string(value))
        return value

    def convert_to(self, data_type, value):
        raise NotImplementedError()


class AppTargetWorkloadsConverter(JsonDataTypeConverter):
    def convert_from(self, data_type, value):
        assert isinstance(data_type, JsonString) and isinstance(
            value, string
        )  # pylint: disable=unidiomatic-typecheck
        if value not in self.targets:
            raise ValueError(
                "Expected a Khulnasoft deployment target, not " + encode_string(value)
            )
        return value

    def convert_to(self, data_type, value):
        assert isinstance(data_type, JsonString) and isinstance(
            value, string
        )  # pylint: disable=unidiomatic-typecheck
        return str(value)

    schema_version_spec = ">=2.0.0"  # supportedDeployments added in version 2.0.0
    targets = ["*", "_search_heads", "_indexers", "_forwarders"]


class AppInputGroup(ObjectView):
    def __init__(self, iterable, onerror=None):

        ObjectView.__init__(self, iterable, onerror)

        if self["description"] is None:
            self["description"] = ""

        requires = self["requires"]

        if requires is None:
            self["requires"] = {}
        else:
            for name in requires:
                value = requires[name]
                requires[name] = tuple() if value is None else tuple(value)

        inputs = self["inputs"]
        self["inputs"] = tuple() if inputs is None else tuple(inputs)

    class Converter(JsonDataTypeConverter):
        def convert_from(self, data_type, value):
            assert isinstance(data_type, JsonObject) and isinstance(value, Mapping)
            return AppInputGroup(((name, value[name]) for name in value))

        def convert_to(self, data_type, value):
            raise NotImplementedError()


class AppInputGroupsSpec(ObjectView):
    class Converter(JsonDataTypeConverter):
        def convert_from(self, data_type, value):
            assert isinstance(data_type, JsonObject) and isinstance(value, Mapping)

            def check(name, value):
                if value is None:
                    raise ValueError("Expected input group " + name + " to be defined")
                if not value.inputs and not value.requires:
                    raise ValueError(
                        "Expected input group "
                        + name
                        + " to have inputs or dependencies defined"
                    )
                return name, value

            return AppInputGroupsSpec((check(name, value[name]) for name in value))

        def convert_to(self, data_type, value):
            raise NotImplementedError()


class AppKhulnasoftReleaseInfo(object):
    def __init__(self, iterable):
        for name, versions in iterable:
            setattr(self, name, tuple(versions))

    # pylint: disable=redefined-builtin
    @classmethod
    def load(cls, file=None):
        if file is None:
            file = path.join(
                slim_configuration.system_config, "khulnasoft-releases.json"
            )
        if isinstance(file, string):
            with io.open(file, encoding="utf-8") as istream:
                return cls._load(istream)
        return cls._load(file)

    # region Protected

    # We include this pylint directive because file is recognized as a built-in even though the standard Python library
    # and we commonly use file as an argument name
    # pylint: disable=redefined-builtin
    @classmethod
    def _load(cls, file):
        return cls.schema.convert_from(json.load(file), onerror=SlimLogger.error)

    # endregion

    class Converter(JsonDataTypeConverter):
        def convert_from(self, data_type, value):
            assert isinstance(data_type, JsonObject) and isinstance(value, Mapping)
            return AppKhulnasoftReleaseInfo(((name, value[name]) for name in value))

        def convert_to(self, data_type, value):
            raise NotImplementedError()

    schema = JsonSchema(
        "Khulnasoft release info",
        JsonValue(
            JsonObject(
                any=JsonValue(
                    JsonArray(JsonValue(JsonString(), converter=JsonVersionConverter()))
                )
            ),
            converter=Converter(),
        ),
    )


class AppKhulnasoftRequirement(ObjectView):
    def __str__(self):
        return ", ".join(
            (
                "Khulnasoft " + edition + " edition " + string(self[edition])
                for edition in self
            )
        )

    class Converter(JsonDataTypeConverter):
        def __init__(self):
            if self._info is None:
                self._info = AppKhulnasoftReleaseInfo.load()

        def convert_from(self, data_type, value):
            assert isinstance(data_type, JsonObject) and isinstance(value, Mapping)

            def convert(name, version_spec):
                try:
                    versions = getattr(self._info, name)
                except AttributeError:
                    raise ValueError(
                        "Expected a Khulnasoft edition name, not " + encode_string(name)
                    )
                if version_spec is None:
                    return name, None
                for version in versions:
                    if version in version_spec:
                        return name, version_spec
                raise ValueError(
                    "Version requirement includes no supported version of Khulnasoft "
                    + name
                    + ": "
                    + string(version_spec)
                )

            return AppKhulnasoftRequirement(
                (convert(name, value[name]) for name in value)
            )

        def convert_to(self, data_type, value):
            raise NotImplementedError()

        _info = None


class AppDeploymentConverter(JsonDataTypeConverter):
    def convert_from(self, data_type, value):
        assert isinstance(data_type, JsonString) and isinstance(
            value, string
        )  # pylint: disable=unidiomatic-typecheck
        if value not in self.deployments:
            raise ValueError(
                "Expected a Khulnasoft deployment type, not " + encode_string(value)
            )
        return value

    def convert_to(self, data_type, value):
        assert isinstance(data_type, JsonString) and isinstance(
            value, string
        )  # pylint: disable=unidiomatic-typecheck
        return str(value)

    schema_version_spec = ">=2.0.0"  # supportedDeployments added in version 2.0.0
    default_deployment = ["_standalone", "_distributed"]
    deployments = ["*", "_standalone", "_distributed", "_search_head_clustering"]


class AppOSConverter(JsonDataTypeConverter):
    def convert_from(self, data_type, value):
        assert isinstance(data_type, JsonString) and isinstance(
            value, string
        )  # pylint: disable=unidiomatic-typecheck
        if value not in self.os_values:
            raise ValueError(
                "Expected an OS type, not %s. Valid types are: %s, or %s."
                % (encode_string(value), ", ".join(SlimTargetOS[:-1]), SlimTargetOS[-1])
            )
        return value

    def convert_to(self, data_type, value):
        assert isinstance(data_type, JsonString) and isinstance(
            value, string
        )  # pylint: disable=unidiomatic-typecheck
        return str(value)

    schema_version_spec = ">=2.0.0"  # targetOS added in version 2.0.0

    default_os = [SlimTargetOSWildcard]
    os_values = SlimTargetOS


class AppManifest(ObjectView):
    @property
    def loaded(self):
        return self._loaded

    @loaded.setter
    def loaded(self, value):
        self._loaded = value

    _loaded = False

    # region Methods

    # pylint disable=redefined-builtin
    def amend(self, app_configuration):
        """Replaces select fields in the current app manifest with information from app.conf."""
        # noinspection PyUnresolvedReferences
        # pylint: disable=no-member
        info = self.info

        info.author = self._get_author(app_configuration)
        info.id = self._get_id(app_configuration)
        info.description = self._get_description(app_configuration)
        info.title = self._get_title(app_configuration)

        def ensure_documentation(name, asset):
            element = info[name]
            if element is None:
                info[name] = ObjectView(
                    (
                        ("name", None),
                        ("text", self._get_text(app_configuration, asset)),
                        ("uri", None),
                    )
                )
            elif element.text is None:
                element.text = self._get_text(app_configuration, asset)

        ensure_documentation("license", "LICENSE")
        ensure_documentation("releaseNotes", "README")
        ensure_documentation("privacyPolicy", "privacy-policy")

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def print_description(self, ostream):

        # type: (TextIO) -> None

        """Writes a description of the manifest in a pretty form

        Does not do dependency checking. The caller should not expect any errors from this function.

        Example:
        [info]
        |-- SLIM fictional test app: A SLIM app for testing Khulnasoft extension packaging, partitioning, and operations.
        |  |-- by David Noble (dnoble@khulnasoft.com) at Khulnasoft, Inc.
        |  |-- packaged as com.khulnasoft.addons-fictional@1.0.0
        [dependencies]
        |-- Khulnasoft Add-on for Microsoft Windows packaged as com.khulnasoft.addon-microsoft_windows@4.7.5
        |-- Khulnasoft Add-on for *nix Operating Systems packaged as com.khulnasoft.addon-star_nix@5.2.1
        [tasks]
        [input-groups]
        |-- Microsoft Windows monitoring defines inputs [input_1, input_2, input_3] and requires no dependencies
        |-- *nix monitoring defines inputs [input_4, input_5] and requires [Khulnasoft Add-on for *nix Operating Systems]
        [incompatible-apps]
        [platform-requirements]

        """

        _ostream = StringIO()
        # The original author probably meant for ostream to only be on py2 with TextIO (see their comments)
        # Nowadays tho, all kinds of different io.* readers get in here as seen by regression
        # testing. In the py2/3 transition, some readers that accepted 'str' now want bytes only.
        # At the end of this function is handling the local _ostream and turning it into what ever makes
        # the callee's ostream.write happy

        # Add the manifest info/dependency/forwarderGroup sections to the payload

        info = self.get("info")
        dependencies = self.get("dependencies")
        tasks = self.get("tasks")
        input_groups = self.get("inputGroups")
        incompatible_apps = self.get("incompatibleApps")
        platform_requirements = self.get("platformRequirements")

        # Define helper functions for formatting manifest details into a readable format

        def get_title(info):
            info_title = info.title if info.title else info.id.name
            info_title += (
                (": " + info.description)
                if "description" in info and info.description
                else ""
            )
            return info_title

        def get_author(author):
            info_author = author.name
            info_author += (
                (" (" + author.email + ")")
                if "email" in author and author.email
                else ""
            )
            info_author += (
                (" at " + author.company)
                if "company" in author and author.company
                else ""
            )
            return info_author

        def get_definition(app_id):
            info_package = app_id.name + " version " + string(app_id.version)
            if "group" in app_id and app_id.group:
                info_package = app_id.group + "-" + info_package
            return info_package

        def get_dependency(app_id, info):
            dependency_info = (
                app_id
                + (" optionally" if info.optional else "")
                + " accepting "
                + string(info.version)
            )
            if info.targetOS != AppOSConverter.default_os:
                if len(info.targetOS) == 1:
                    os_str = info.targetOS[0]
                else:
                    os_str = "[" + ", ".join((os for os in info.targetOS)) + "]"
                dependency_info += " on " + os_str
            dependency_info += (
                " (packaged as " + info.package + ")"
                if "package" in info and info.package
                else ""
            )
            return dependency_info

        def get_inputs(group, info):
            text = group

            if info.inputs:
                text += (
                    " defines inputs [" + ", ".join((name for name in info.inputs))
                ) + "]"
            else:
                text += " defines no inputs"

            if info.requires:
                text += (
                    " and requires ["
                    + ", ".join((name for name in info.requires))
                    + "]"
                )
            else:
                text += " and requires no dependencies"

            return text

        _ostream.write("[info]\n")
        if info is not None:
            _ostream.write("|-- " + get_title(info) + "\n")
            if "author" in info and info.author:
                for author in info.author:
                    _ostream.write("|  |-- by " + get_author(author) + "\n")
            _ostream.write("|  |-- defined as " + get_definition(info.id) + "\n")

        _ostream.write("[dependencies]\n")
        # print('[dependencies]', file=_ostream)

        if dependencies is not None:
            for app_id, info in list(dependencies.items()):
                _ostream.write("|-- " + get_dependency(app_id, info) + "\n")

        _ostream.write("[tasks]\n")
        if tasks is not None:
            for task in tasks:
                s = "|-- " + task + "\n"  # pylint: disable=invalid-name
                _ostream.write(s)

        _ostream.write("[input-groups]\n")
        if input_groups is not None:
            for group, info in list(input_groups.items()):
                _ostream.write("|-- " + get_inputs(group, info) + "\n")

        _ostream.write("[incompatible-apps]\n")
        if incompatible_apps is not None:
            for app_id in incompatible_apps:
                s = (
                    "|-- "
                    + app_id
                    + " version range "
                    + str(incompatible_apps[app_id])
                    + "\n"
                )  # nopep8, pylint: disable=invalid-name
                _ostream.write(s)

        _ostream.write("[platform-requirements]\n")
        if platform_requirements is not None:
            _ostream.write("|-- " + str(platform_requirements.khulnasoft) + "\n")

        try:
            ostream.write(_ostream.getvalue())
        except:
            ostream.write(_ostream.getvalue().encode())

    @classmethod
    def generate(cls, app_configuration, ostream, add_defaults=True):
        """Generate an AppManifest object from the AppConfiguration object.

        Resulting manifest is saved to the ostream. Caller is required to check for logged errors on return.

        """
        app_root = app_configuration.app_root

        manifest_tuple = (
            ("schemaVersion", cls._schema_version),
            (
                "info",
                ObjectView(
                    (
                        ("title", cls._get_title(app_configuration)),
                        ("id", cls._get_id(app_configuration)),
                        ("author", cls._get_author(app_configuration)),
                        ("releaseDate", None),
                        ("description", cls._get_description(app_configuration)),
                        (
                            "classification",
                            ObjectView(
                                (
                                    ("intendedAudience", None),
                                    ("categories", []),
                                    ("developmentStatus", None),
                                )
                            ),
                        ),
                        ("commonInformationModels", None),
                        (
                            "license",
                            ObjectView(
                                (
                                    ("name", None),
                                    (
                                        "text",
                                        cls._get_text(app_configuration, "LICENSE"),
                                    ),
                                    ("uri", None),
                                )
                            ),
                        ),
                        (
                            "privacyPolicy",
                            ObjectView(
                                (
                                    ("name", None),
                                    (
                                        "text",
                                        cls._get_text(
                                            app_configuration, "privacy-policy"
                                        ),
                                    ),
                                    ("uri", None),
                                )
                            ),
                        ),
                        (
                            "releaseNotes",
                            ObjectView(
                                (
                                    ("name", None),
                                    (
                                        "text",
                                        cls._get_text(app_configuration, "README"),
                                    ),
                                    ("uri", None),
                                )
                            ),
                        ),
                    )
                ),
            ),
        )

        manifest_defaults = """
# The following sections can be customized and added to the manifest. For detailed information,
# see the documentation at http://dev.khulnasoft.com/view/packaging-toolkit/SP-CAAAE9V
#
# Lists the app dependencies and version requirements
# "dependencies": {
#     "<app-group>:<app-name>": {
#         "version": "*",
#         "package": "<source-package-name>",
#         "optional": [true|false]
#     }
# }
#
# Lists the inputs that belong on the search head rather than forwarders
# "tasks": []
#
# Lists the possible input groups with app dependencies, and inputs that should be included
# "inputGroups": {
#     "<group-name>": {
#         "requires": {
#             "<app-group>:<app-name>": ["<dependent-input-groups>"]
#         },
#         "inputs": ["<defined-inputs>"]
#     }
# }
#
# Lists the app IDs that cannot be installed on the system alongside this app
# "incompatibleApps": {
#     "<app-group>:<app-name>": "<version>"
# }
#
# Specify the platform version requirements for this app
# "platformRequirements": {
#     "khulnasoft": {
#         "Enterprise": "<version>"
#     }
# }
#
# Lists the supported deployment types this app can be installed on
# "supportedDeployments": ["*" | "_standalone" | "_distributed" | "_search_head_clustering"]
#
# Lists the targets where app can be installed to
# "targetWorkloads": ["*" | "_search_heads" | "_indexers" | "_forwarders"]
#
"""
        # Construct the manifest

        current_directory = os.getcwd()
        os.chdir(app_root)

        try:
            manifest = AppManifest(manifest_tuple)
        finally:
            os.chdir(current_directory)

        # Optionally save the manifest

        if ostream is not None:
            if not SlimLogger.error_count():
                with ostream:
                    if ostream != sys.stdout:
                        ostream.truncate(0)  # truncate the existing manifest file
                    manifest.save(ostream, indent=True)
                    if add_defaults:
                        ostream.write(manifest_defaults)
            elif ostream != sys.stdout:
                ostream.close()

        return manifest

    # pylint: disable=redefined-builtin
    # noinspection PyProtectedMember
    @classmethod
    def load(cls, file):
        if isinstance(file, string):
            with io.open(file, encoding="utf-8") as istream:
                app_manifest = cls._load(istream)
        else:
            app_manifest = cls._load(file)
        return app_manifest

    # noinspection PyProtectedMember
    @classmethod
    def schema_version(cls):
        """Return the schema version being used to handle AppManifest objects."""
        return cls._schema_version

    # endregion

    # region Protected

    _schema_version = "2.0.0"
    _schema_version_spec = ">=1.0.0"

    schema = JsonSchema(
        "manifest",
        JsonValue(
            required=True,
            data_type=JsonObject(
                JsonField(
                    "schemaVersion",
                    JsonString(),
                    converter=JsonVersionConverter(_schema_version_spec),
                    required=True,
                ),
                JsonField(
                    "info",
                    required=True,
                    data_type=JsonObject(
                        JsonField("title", JsonString()),
                        JsonField(
                            "id",
                            JsonObject(
                                JsonField("group", JsonString()),
                                JsonField("name", JsonString(), required=True),
                                JsonField(
                                    "version",
                                    JsonString(),
                                    converter=JsonVersionConverter(),
                                ),
                            ),
                            required=True,
                        ),
                        JsonField(
                            "author",
                            JsonArray(
                                JsonValue(
                                    JsonObject(
                                        JsonField("name", JsonString(), required=True),
                                        JsonField("email", JsonString()),
                                        JsonField("company", JsonString()),
                                    )
                                )
                            ),
                        ),
                        JsonField("releaseDate", JsonString()),  # TODO: date converter
                        JsonField("description", JsonString()),
                        JsonField(
                            "classification",
                            JsonObject(  # TODO: classification class and class converter
                                JsonField("intendedAudience", JsonString()),
                                JsonField(
                                    "categories", JsonArray(JsonValue(JsonString()))
                                ),
                                JsonField("developmentStatus", JsonString()),
                            ),
                        ),
                        JsonField(
                            "commonInformationModels",
                            JsonObject(
                                any=JsonValue(
                                    JsonString(), converter=JsonVersionSpecConverter()
                                ),
                                converter=AppCommonInformationModelSpec.Converter(),
                            ),
                        ),
                        JsonField(
                            "license",
                            JsonObject(
                                JsonField("name", JsonString()),
                                JsonField(
                                    "text",
                                    JsonString(),
                                    converter=JsonFilenameConverter(),
                                ),
                                JsonField("uri", JsonString()),
                            ),
                        ),
                        JsonField(
                            "privacyPolicy",
                            JsonObject(
                                JsonField("name", JsonString()),
                                JsonField(
                                    "text",
                                    JsonString(),
                                    converter=JsonFilenameConverter(),
                                ),
                                JsonField("uri", JsonString()),
                            ),
                        ),
                        JsonField(
                            "releaseNotes",
                            JsonObject(
                                JsonField("name", JsonString()),
                                JsonField(
                                    "text",
                                    JsonString(),
                                    converter=JsonFilenameConverter(),
                                ),
                                JsonField("uri", JsonString()),
                            ),
                        ),
                    ),
                ),
                JsonField(
                    "dependencies",
                    JsonObject(
                        any=JsonValue(
                            JsonObject(
                                JsonField(
                                    "version",
                                    JsonString(),
                                    converter=JsonVersionSpecConverter(),
                                    default=JsonVersionSpecConverter.any_version,
                                ),
                                JsonField(
                                    "package",
                                    JsonString(),
                                    converter=AppDependencyPackageConverter(),
                                ),
                                JsonField("optional", JsonBoolean(), default=False),
                                JsonField(
                                    "targetOS",
                                    JsonArray(
                                        JsonValue(
                                            JsonString(), converter=AppOSConverter()
                                        )
                                    ),
                                    default=AppOSConverter.default_os,
                                    version=AppOSConverter.schema_version_spec,
                                ),
                            ),
                            converter=AppDependency.Converter(),
                        )
                    ),
                ),
                JsonField("tasks", JsonArray(JsonValue(JsonString()))),
                JsonField(
                    "inputGroups",
                    JsonObject(
                        any=JsonValue(
                            JsonObject(
                                JsonField(
                                    "requires",
                                    JsonObject(
                                        any=JsonValue(
                                            JsonArray(JsonValue(JsonString()))
                                        )
                                    ),
                                ),
                                JsonField("inputs", JsonArray(JsonValue(JsonString()))),
                                JsonField("description", JsonString()),
                            ),
                            converter=AppInputGroup.Converter(),
                        )
                    ),
                    converter=AppInputGroupsSpec.Converter(),
                ),
                JsonField(
                    "incompatibleApps",
                    JsonObject(
                        any=JsonValue(
                            JsonString(),
                            converter=JsonVersionSpecConverter(),
                            required=True,
                        )
                    ),
                ),
                JsonField(
                    "platformRequirements",
                    JsonObject(
                        JsonField(
                            "khulnasoft",
                            JsonObject(
                                any=JsonValue(
                                    JsonString(),
                                    converter=JsonVersionSpecConverter(),
                                    required=True,
                                )
                            ),
                            converter=AppKhulnasoftRequirement.Converter(),
                        )
                    ),
                ),
                JsonField(
                    "supportedDeployments",
                    JsonArray(
                        JsonValue(JsonString(), converter=AppDeploymentConverter())
                    ),
                    default=AppDeploymentConverter.default_deployment,
                    version=AppDeploymentConverter.schema_version_spec,
                ),
                JsonField(
                    "targetWorkloads",
                    JsonArray(
                        JsonValue(JsonString(), converter=AppTargetWorkloadsConverter())
                    ),
                    version=AppTargetWorkloadsConverter.schema_version_spec,
                ),
            ),
        ),
    )

    @staticmethod
    def _get_author(app_configuration):
        """Construct the info.author section of the app manifest (no default)"""
        # Note that we do not complain that, if any of the author values (name, email, or company) are missing
        # Note also that we do not ensure the name, email, company tuples are unique
        app = app_configuration.get("app")

        if app is not None:

            author = [
                ObjectView(
                    (
                        ("name", stanza.name[len("author=") :]),
                        ("email", stanza.get_value("email")),
                        ("company", stanza.get_value("company")),
                    )
                )
                for stanza in app.stanzas()
                if stanza.name.startswith("author=")
            ]

            if len(author) > 0:
                return author

        name = app_configuration.get_value("app", "launcher", "author")

        if not name:
            author = []  # No author specified
        else:
            author = [ObjectView((("name", name), ("email", None), ("company", None)))]

        return author

    @staticmethod
    def _get_description(app_configuration):
        return app_configuration.get_value("app", "launcher", "description")

    @staticmethod
    def _get_id(app_configuration):
        """Construct the info.id section of the app manifest"""
        group, name, version = app_configuration.get_value(
            "app", "id", ("group", "name", "version")
        )

        def normalize_version(stanza, value):
            if value is None:
                SlimLogger.error(
                    "A value for version in the [id] stanza of app.conf is required"
                )
                return "0.0.0"
            try:
                value = Version.coerce(value)
            except ValueError:
                SlimLogger.error(
                    "Expected a semantic version number as the value of version in the [",
                    stanza,
                    "] stanza " "of app.conf, not ",
                    encode_string(value),
                )
                value = "0.0.0"
            else:
                value = string(value)
            return value

        if (group, name, version) == (None, None, None):

            # Legacy code path which is less strict; the [id] stanza of app.conf is absent

            name = AppManifest._get_package_id(
                app_configuration, path.basename(app_configuration.app_root)
            )
            version = normalize_version(
                "launcher", app_configuration.get_value("app", "launcher", "version")
            )
        else:

            # New code path which is more strict; the [id] stanza of app.conf is present

            # Validate app ID:
            # * <id.name> is
            # * [<id.group>-]<id.name> must equal <package.id>, if <package.id> is specified

            folder_name = path.basename(app_configuration.app_root)

            if name is None:
                SlimLogger.error(
                    "A value for name in the [id] stanza of app.conf is required"
                )
                name = folder_name  # short-circuits a downstream error message
            else:
                computed_id = "-".join(
                    value for value in (group, name) if value is not None
                )
                alt_id = AppManifest._get_package_id(app_configuration, computed_id)
                if alt_id != computed_id:
                    SlimLogger.error(
                        "The combination of group and name from the [id] stanza of app.conf (",
                        computed_id,
                        ") "
                        "must equal the value of id in the [package] stanza of app.conf (",
                        alt_id,
                        ")",
                    )
                if folder_name != computed_id:
                    SlimLogger.error(
                        "The combination of group and name from the [id] stanza of app.conf (",
                        computed_id,
                        ") " "must equal the name of the app folder (",
                        folder_name,
                        ")",
                    )
                    name = folder_name  # short-circuits a downstream error message

            # Validate app version number:
            # * <id.version> is required
            # * <id.version> must equal <launcher.version>, if <launcher.version> is specified

            version = normalize_version("id", version)
            alt_version = app_configuration.get_value("app", "launcher", "version")

            if alt_version is not None:
                alt_version = normalize_version("launcher", alt_version)
                if alt_version != version:
                    SlimLogger.error(
                        "Expected the value of version in the [launcher] stanza of app.conf (",
                        encode_string(alt_version),
                        " to equal the value of version in the "
                        "[id] stanza of app.conf (",
                        encode_string(version),
                        ")",
                    )

        return ObjectView((("group", group), ("name", name), ("version", version)))

    @staticmethod
    def _get_package_id(app_configuration, default_value):
        value = app_configuration.get_value("app", "package", "id")
        if value is None:
            SlimLogger.warning(
                "There is no value for id in the [package] stanza of app.conf"
            )
            value = default_value
        return value

    @staticmethod
    def _get_text(app_configuration, name):
        """Construct info.[license|privacyPolicy|releaseNotes].text element of the app manifest."""
        partial_filename = path.join(app_configuration.app_root, name)
        for extension in ".md", ".rtf", ".txt":
            filename = partial_filename + extension
            if path.isfile(filename):
                return "./" + path.basename(filename)
        return None

    @staticmethod
    def _get_title(app_configuration):
        """Construct the info.title element of the app manifest (no default)."""
        return app_configuration.get_value("app", "ui", "label")

    @classmethod
    def _load(cls, istream):
        """Load an AppManifest object from `istream`.

        Parse out any comment lines. Caller is required to check for logged errors on return.

        """
        text = "".join(
            line for line in istream if re.match(r"\s*#", line) is None
        )  # confirmed re.match copies no text

        try:
            object_view = json.loads(
                text, object_pairs_hook=AppManifest._create_object_view
            )
        except ValueError as error:
            SlimLogger.error(
                "Failed to load app manifest from ",
                encode_filename(istream.name),
                ": ",
                error,
            )
            object_view = ObjectView.empty

        current_directory = os.getcwd()
        os.chdir(path.dirname(istream.name))

        try:
            app_manifest = AppManifest(object_view)
            app_manifest.loaded = True
        finally:
            os.chdir(current_directory)

        return app_manifest

    # endregion
    pass  # pylint: disable=unnecessary-pass
