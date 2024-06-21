# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from abc import ABCMeta
from collections import OrderedDict

from os import path
import os

import tarfile

import io
import shutil
from future.utils import with_metaclass

from semantic_version import Version, Spec

from slim.utils.public import SlimTargetOSWildcard
from ..utils import *
from ..utils.internal import string

from ._configuration import AppConfiguration
from ._deployment import AppDeploymentSpecification
from ._internal import ObjectView
from ._manifest import AppManifest, AppDeploymentConverter


class _AppSourceFactory(ABCMeta):
    def __call__(cls, *args, **kwargs):
        package_path = args[0]
        if path.isdir(package_path):
            app_source = super(_AppSourceFactory, cls).__call__(*args, **kwargs)
        else:
            package = path.basename(package_path)
            try:
                app_source = slim_configuration.cache.get_sources[package]
                app_source.package = package_path
            except KeyError:
                app_source = super(_AppSourceFactory, cls).__call__(*args, **kwargs)
                slim_configuration.cache.add_source(package, app_source)
        return app_source


# pylint: disable=no-member
class AppSource(with_metaclass(_AppSourceFactory, ObjectView)):

    __slots__ = (
        "_configuration",
        "_container",
        "_dependencies",
        "_dependency_sources",
        "_directory",
        "_id",
        "_manifest",
        "_package_prefix",
        "_qualified_id",
        "_version",
    )

    def __init__(self, package, local_conf=None):
        """Get an AppSource object given a source package/directory, maybe from the cache.

        Local configuration can be provided to update the app source. Caller is required to check for logged errors.

        """
        # pylint: disable=non-parent-init-called
        ObjectView.__init__(
            self,
            (
                ("package", path.abspath(package)),
                (
                    "local_conf",
                    None if local_conf is None else path.abspath(local_conf),
                ),
            ),
        )  # pylint: disable=protected-access
        self._configuration = (
            self._container
        ) = self._dependencies = self._dependency_sources = self._directory = None
        self._id = (
            self._manifest
        ) = self._package_prefix = self._qualified_id = self._version = None
        self._description = None

        if not path.exists(self.package):
            SlimLogger.error("Package not found: ", self.package)
            return  # do not try to validate a package that does not exist

        self._validate_input_groups()
        self._validate_identity()
        self._validate_tasks()
        self._validate_deployments()

    # region Special methods

    def __eq__(self, other):
        return self.id.__eq__(other.id)

    def __hash__(self):
        return self.id.__hash__()

    # endregion

    # region Properties

    @property
    def configuration(self):
        value = self._configuration
        if value is None:
            app_root = self.directory
            if self.local_conf is not None:
                with tarfile.open(self.local_conf) as local_conf:
                    local_conf.extractall(app_root)
            value = self._configuration = AppConfiguration.load(app_root)
        return value

    @property
    def container(self):
        return self._get_field_value("_container")

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def dependency_sources(self):
        return self._get_field_value("_dependency_sources")

    @property
    def description(self):
        # type: () -> dict

        description = self._description

        if description is None:

            app_manifest = self.manifest
            # pylint: disable=protected-access
            description = ObjectView._to_dict(
                (
                    ("info", app_manifest.info),
                    ("dependencies", app_manifest.dependencies),
                    ("tasks", app_manifest.tasks),
                    ("input_groups", app_manifest.inputGroups),
                    ("incompatible_apps", app_manifest.incompatibleApps),
                    ("platform_requirements", app_manifest.platformRequirements),
                    ("supported_deployments", app_manifest.supportedDeployments),
                    ("schema_version", app_manifest.schemaVersion),
                    ("generated", not app_manifest.loaded),
                )
            )
            self._description = description

        return description

    @property
    def directory(self):
        return self._get_field_value("_directory")

    # pylint: disable=invalid-name
    @property
    def id(self):
        value = self._id
        if value is None:
            identity = self.manifest.info.id
            value = self._id = "-".join(
                value for value in (identity.group, identity.name) if value is not None
            )
        return value

    @property
    def manifest(self):
        return self._get_field_value("_manifest")

    @property
    def package_prefix(self):
        value = self._package_prefix
        if value is None:
            app_id = self.manifest.info.id.get
            value = self._package_prefix = "-".join(
                [
                    string(part)
                    for part in [app_id("group"), app_id("name"), app_id("version")]
                    if part is not None
                ]
            )
        return value

    @property
    def qualified_id(self):
        value = self._qualified_id
        if value is None:
            value = self._qualified_id = (
                self.id + ":" + string(self.manifest.info.id.version)
            )
        return value

    @property
    def version(self):
        value = self._version
        if value is None:
            value = self._version = self.manifest.info.id.version
        return value

    # endregion

    # region Methods

    def get_dependencies_for_target_os(self, target_os):
        """
        :param target_os: if not None, select only dependencies for the given target OS, otherwise, select all
        :return: Matched dependencies
        """
        for app_id, app in list(self.manifest.dependencies.items()):
            if target_os == SlimTargetOSWildcard:
                yield app_id, app
                continue

            if SlimTargetOSWildcard in app.targetOS:
                yield app_id, app
                continue

            if target_os in app.targetOS:
                yield app_id, app
                continue

    def populate_dependency_sources(
        self, app_dependencies_dir, installed_packages=None
    ):
        """
        Populates the AppSource dependencies from the given directory, into more AppSource objects.  Returns all
        *nested* dependencies, required for the AppDependencyGraph operations.

        """
        dependencies = self.manifest.dependencies
        dependency_sources = OrderedDict()

        if dependencies is not None:
            for name in dependencies:
                dependency = dependencies[name]

                # If the manifest does not define a packaged dependency, check the list of installed app packages
                if dependency.package:
                    package = dependency.package
                elif installed_packages and installed_packages.get(name):
                    package = installed_packages.get(name)
                else:
                    continue

                location = path.join(app_dependencies_dir, package)
                if path.isfile(location) and tarfile.is_tarfile(location):
                    dependency_source = AppSource(location)
                    dependency_sources[package] = dependency_source
                    dependency_sources.update(dependency_source.dependency_sources)

        return dependency_sources

    def print_description(self, ostream):
        # type: (typing.TextIO) -> None
        self.manifest.print_description(ostream)

    def validate_deployment_specification(self, deployment_specification):

        input_groups = self.manifest.get("inputGroups")

        # TODO: Invert these two methods by way of methods on a deployment specification, something like this:
        #
        #   deployment_specification.includes_all_input_groups
        #   deployment_specification.includes_no_input_groups
        #
        # Think about the possibility of a single method, not two methods as indicated above

        if AppDeploymentSpecification.is_all_input_groups(
            deployment_specification.inputGroups
        ):
            return
        if AppDeploymentSpecification.are_no_input_groups(
            deployment_specification.inputGroups
        ):
            return
        if input_groups is None:
            SlimLogger.error(
                "Deployment specification includes input groups, but ",
                self.qualified_id,
                " defines no input groups: ",
                deployment_specification,
            )
            return

        for name in deployment_specification.inputGroups:
            try:
                if getattr(input_groups, name) is ObjectView.empty:
                    raise AttributeError
            except AttributeError:
                SlimLogger.error(
                    "Deployment specification requests group ",
                    encode_string(name),
                    " but that group is not defined " "by ",
                    self.qualified_id,
                    ": ",
                    deployment_specification,
                )

    # endregion

    # region Protected

    _file_types = {
        b"0": "regular file",
        b"\0": "regular file",
        b"1": "link",
        b"2": "symbolic link",
        b"3": "character special device",
        b"4": "block special device",
        b"5": "directory",
        b"6": "FIFO special device",
        b"7": "contiguous file",
    }

    def _extract_source(self):

        package_name = path.basename(self.package)
        file_type = AppSource._file_type

        if package_name.endswith(".tar.gz"):
            package_name = package_name[: -len(".tar.gz")]
        elif (
            package_name.endswith(".tgz")
            or package_name.endswith(".tar")
            or package_name.endswith(".spl")
        ):
            package_name = package_name[: -len(".spl")]

        app_container = path.join(
            slim_configuration.cache.cache_path, package_name + ".source"
        )
        app_root = ""

        with tarfile.open(self.package) as package:

            # Verify that the app is composed of a single root-level directory optionally followed by .dependencies

            member = package.next()

            if member is None:
                raise SlimError(
                    package.name,
                    ": Expected a source package, not an empty tar archive",
                )

            app_root = member.name
            parent = path.dirname(app_root)

            if parent == "":
                if not member.isdir():
                    raise SlimError(
                        package.name,
                        ": Expected the first member of this source package to be a directory, but it is "
                        "a ",
                        file_type(member),
                        ": ",
                        app_root,
                    )
            else:
                while parent not in ("", "."):
                    app_root = parent
                    parent = path.dirname(app_root)

            validate_tarinfo = AppSource._validate_tarinfo_of_app_root

            for member in iter(package.next, None):
                validate_tarinfo = validate_tarinfo(member, app_root, package.name)

            # Remove the app, if it's present in the file system, and then extract all files from the source package

            if path.isdir(app_container):
                shutil.rmtree(app_container)
            if path.isfile(app_container) or path.islink(app_container):
                os.remove(app_container)

            package.extractall(app_container)

        self._directory = path.abspath(path.join(app_container, app_root))
        self._container = app_container

    @classmethod
    def _file_type(cls, tarinfo):
        type_code = tarinfo.type
        try:
            return cls._file_types[type_code]
        except KeyError:
            return "file of type " + string(type_code)

    def _get_field_value(self, name):
        """Common get function for top-level fields: _container, _dependency_sources, _directory.

        If the field does not exist, the fields have not been initialized based on the app_root type. Extract the
        app_root tarball or initialize the fields to default values.

        """
        value = getattr(self, name)

        if value is None:

            app_root = self.package

            if path.isdir(app_root):
                self._directory = self._container = app_root
            else:
                try:
                    self._extract_source()
                except SlimError as error:
                    SlimLogger.error(error)
                    return None

            # Load or generate app manifest

            filename = path.join(self.directory, "app.manifest")

            if path.isfile(filename):
                app_manifest = AppManifest.load(filename)
            else:
                SlimLogger.information(
                    "Generating app manifest for "
                    + os.path.basename(self.package)
                    + "..."
                )
                app_configuration = self._configuration = AppConfiguration.load(
                    self.directory
                )
                app_manifest = AppManifest.generate(
                    app_configuration, io.open(filename, "wb"), add_defaults=False
                )

            self._manifest = app_manifest

            # Construct collection of app dependency sources (after we have the other values set)

            app_dependencies_dir = path.abspath(
                path.join(self.container, SlimConstants.DEPENDENCIES_DIR)
            )

            if not path.exists(app_dependencies_dir):
                app_dependencies_dir = path.abspath(slim_configuration.repository_path)

            self._dependency_sources = self.populate_dependency_sources(
                app_dependencies_dir
            )
            value = getattr(self, name)

        return value

    # pylint: disable=too-many-branches
    def _validate_input_groups(self):

        input_groups = self.manifest.inputGroups
        inputs = self.configuration.get("inputs")

        if input_groups is not None:

            if inputs is None:

                # Verify that no input group has inputs

                for group_name in input_groups:
                    info = input_groups[group_name]
                    input_names = info.inputs
                    if not input_names:
                        continue
                    if len(input_names) == 1:
                        SlimLogger.warning(
                            self.package,
                            ": ",
                            self.qualified_id,
                            " manifest lists this undefined input in forwarder "
                            "group ",
                            encode_string(group_name),
                            ": ",
                            encode_string(input_names[0]),
                        )
                    else:
                        SlimLogger.warning(
                            self.package,
                            ": ",
                            self.qualified_id,
                            " manifest lists these undefined inputs in " "input group ",
                            encode_string(group_name),
                            ": ",
                            encode_series(
                                (
                                    encode_string(input_name)
                                    for input_name in input_names
                                )
                            ),
                        )
            else:

                # Verify that no input group has undefined inputs

                for group_name in input_groups:
                    info = input_groups[group_name]
                    input_names = info.inputs
                    if not input_names:
                        continue
                    for input_name in input_names:
                        if inputs.has(input_name):
                            continue
                        SlimLogger.warning(
                            self.package,
                            ": ",
                            self.qualified_id,
                            " manifest lists this undefined input in forwarder "
                            "group ",
                            encode_string(group_name),
                            ": ",
                            encode_string(input_name),
                        )

            # Verify that all input group dependencies are listed in the dependencies section
            # It is an error, not a warning because we cannot deploy without them

            dependencies = self.manifest.dependencies

            for group_name in input_groups:
                group = input_groups[group_name]
                group_requires = group.requires
                if group_requires is None:
                    continue
                remove_list = []
                for dependency_name in group_requires:
                    if dependencies and dependency_name in dependencies:
                        continue
                    SlimLogger.error(
                        self.package,
                        ": ",
                        self.qualified_id,
                        " manifest declares that input group ",
                        group_name,
                        " requires ",
                        dependency_name,
                        ", but ",
                        dependency_name,
                        " is not declared to be a " "dependency of ",
                        self.qualified_id,
                    )
                    remove_list.append(dependency_name)
                for dependency_name in remove_list:
                    del group_requires[dependency_name]

    def _validate_identity(self):

        # noinspection PyShadowingNames
        def to_app_id(triple):
            if triple is None:
                return None, None, None
            group, name, version = triple
            if version is not None:
                try:
                    # noinspection PyProtectedMember
                    version._setting._value = Version.coerce(
                        version.value
                    )  # pylint: disable=all
                except ValueError:
                    # TODO: Dnoble: incorporate this logic into FilePosition.__str__:
                    # file, line = version.position.file, version.position.line
                    # file = file[len(path.commonprefix((file, path.dirname(self.directory)))) + 1:]
                    # position = FilePosition(file, line)
                    SlimLogger.error(
                        version.position, ": Expected version number, not ", version
                    )
                    # SPL-180633: making behaviour the same as in _manifest.py
                    version._setting._value = Version.coerce("0.0.0")
            return group, name, version

        if self.manifest.info is None:
            SlimLogger.error("App manifest info is missing or incorrect")
            return

        manifest_id = self.manifest.info.id

        assert manifest_id is not None
        assert manifest_id.name is not None
        assert manifest_id.version is not None

        conf = self.configuration.get("app")

        if conf is not None:
            legacy_id = to_app_id(
                (None, conf.get("package", "id"), conf.get("launcher", "version"))
            )
            configuration_id = to_app_id(conf.get("id", ("group", "name", "version")))

            if configuration_id == (None, None, None):
                group, name, version = legacy_id
            else:
                group, name, version = configuration_id

                if name is None:
                    name = legacy_id[1]
                elif legacy_id[1] is not None and name != legacy_id[1]:
                    SlimLogger.error(
                        name.position,
                        ": App ",
                        name,
                        " does not match ",
                        legacy_id[1],
                        " at ",
                        legacy_id[1].position,
                    )

                if version is None:
                    version = legacy_id[2]
                elif legacy_id[2] is not None and version != legacy_id[2]:
                    SlimLogger.error(
                        version.position,
                        ": App ",
                        version,
                        " does not match ",
                        legacy_id[2],
                        " at ",
                        legacy_id[2].position,
                    )

            if group is not None and group.value != manifest_id.group:
                SlimLogger.error(
                    group.position,
                    ": App ",
                    group,
                    " does not match manifest.info.id.group = ",
                    manifest_id.group,
                )

            if name is not None and name.value != manifest_id.name:
                SlimLogger.error(
                    name.position,
                    ": App ",
                    name,
                    " does not match manifest.info.id.name = ",
                    manifest_id.name,
                )

            if version is not None and version.value != manifest_id.version:
                SlimLogger.error(
                    version.position,
                    ": App ",
                    version,
                    " does not match manifest.info.id.version = ",
                    manifest_id.version,
                )

        app_root = path.basename(self.directory)

        if app_root != self.id:
            SlimLogger.error(
                "App folder name ",
                encode_filename(app_root),
                " does not match App ID ",
                encode_filename(self.id),
            )

    @classmethod
    def _validate_tarinfo_of_app_root(cls, member, app_root, package_name):

        if path.commonprefix((app_root, member.name)) == app_root:
            return cls._validate_tarinfo_of_app_root

        if member.name != SlimConstants.DEPENDENCIES_DIR:
            raise SlimError(
                package_name,
                ": Expected all members of this source package to be contained by ",
                app_root,
                " or its ",
                SlimConstants.DEPENDENCIES_DIR,
                " directory, but this file is not: ",
                member.name,
            )

        if not member.isdir():
            raise SlimError(
                package_name,
                ": Expected ",
                SlimConstants.DEPENDENCIES_DIR,
                " to be a directory, " "but it is a ",
                cls._file_type(member),
            )

        return cls._validate_tarinfo_of_packaged_dependencies

    @classmethod
    def _validate_tarinfo_of_packaged_dependencies(cls, member, app_root, package_name):

        if (
            not path.commonprefix((SlimConstants.DEPENDENCIES_DIR, member.name))
            == SlimConstants.DEPENDENCIES_DIR
        ):
            raise SlimError(
                package_name,
                ": Expected all members of this source package to be contained by ",
                app_root,
                " or its ",
                SlimConstants.DEPENDENCIES_DIR,
                " directory, but this file is not: ",
                member.name,
            )

        if not member.isfile():
            raise SlimError(
                package_name,
                ": Expected all members of the ",
                SlimConstants.DEPENDENCIES_DIR,
                " directory to be " "tar archives, but this is a ",
                cls._file_type(member),
                ": ",
                member.name,
            )

        return cls._validate_tarinfo_of_packaged_dependencies

    def _validate_tasks(self):
        tasks = self.manifest.tasks

        if tasks is not None:
            inputs = self.configuration.get("inputs")
            undefined_tasks = (
                tasks
                if inputs is None
                else [task for task in tasks if inputs.has(task) is False]
            )

            if len(undefined_tasks) > 0:
                SlimLogger.warning(
                    self.package,
                    ": ",
                    self.qualified_id,
                    " manifest lists these undefined tasks: ",
                    encode_series((encode_string(task) for task in undefined_tasks)),
                )

    def _validate_deployments(self):
        schema_version = self.manifest.schemaVersion
        deployments = self.manifest.supportedDeployments

        # The deployments field must not be none or empty if the manifest schema version
        # supports the deployment specification and we loaded the manifest from a file
        # ie, if we generated this manifest on the fly then this field is not required
        version_spec = Spec(AppDeploymentConverter.schema_version_spec)
        if (
            self.manifest.loaded
            and not deployments
            and version_spec.match(schema_version)
        ):
            SlimLogger.error(
                path.basename(self.package),
                ": Expected at least one supported deployment type to be defined. "
                "Update the app.manifest to include the supportedDeployments field.",
            )

    # endregion
    pass  # pylint: disable=unnecessary-pass
