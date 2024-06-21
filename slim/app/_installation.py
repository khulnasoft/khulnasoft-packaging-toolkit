# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

""" app_installation module

The app_installation module defines this class hierarchy:

  AppServerClassCollection
  |
  └-> # (name: string, AppServerClass) *
                       |
                       ├-> name: string
                       |
                       ├-> workload: frozenset ( 1*("searchHead" / "indexer" / "forwarder") | ("*") )
                       |
                       └-> AppInstallationGraph 1
                           |
                           └-> (app_id: string, AppInstallation) *
                                                |
                                                ├-> (app_id: string, dependency: AppInstallationDependency) *
                                                |
                                                ├-> (app_id: string, dependent: AppInstallation) *
                                                |
                                                ├-> (app_id: string, (input_group: string) *) *
                                                |
                                                ├-> is_root: bool
                                                |
                                                └-> source: AppSource 1

"""

from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import object
from collections import (
    Iterable,
    Mapping,
    OrderedDict,
    deque,
)  # pylint: disable=no-name-in-module
from json import JSONEncoder
from os import path

import semantic_version
from semantic_version import Version

from ..utils import (
    SlimStatus,
    SlimLogger,
    SlimInstallationGraphActions,
    encode_string,
    slim_configuration,
)
from ..utils.internal import string

from ._deployment import AppDeploymentPackage, AppDeploymentSpecification
from ._internal import ObjectView, OrderedSet


class _AppJsonEncoder(JSONEncoder):
    def __init__(self, indent=False):
        if indent:
            separators = None
            indent = 2
        else:
            separators = (",", ":")
            indent = None
        JSONEncoder.__init__(
            self, ensure_ascii=False, indent=indent, separators=separators
        )

    def default(self, value):  # pylint: disable=arguments-differ, method-hidden
        # Under Python 2.7 pylint incorrectly asserts AppJsonEncoder.default is hidden by an attribute defined in
        # json.encoder line 162. Code inspection reveals this not to be the case, hence we disable the
        # method-hidden message
        if isinstance(value, Iterable):
            return list(value)
        return JSONEncoder.default(self, value)


_encoder = _AppJsonEncoder()
_encode = _encoder.encode
_iterencode = _encoder.iterencode


# pylint: disable=too-many-public-methods


class AppInstallation(object):
    def __init__(self, server_class, app_info):
        def source():
            try:
                app_id, app_version, app_package = (
                    app_info["id"],
                    app_info["version"],
                    app_info["source"],
                )
            except KeyError:
                app_package = server_class.get_source(app_info["source"])
            else:
                app_package = server_class.get_source(app_id, app_version, app_package)
            return app_package

        def version():
            try:
                value = app_info["version"]
            except KeyError:
                pass
            else:
                if isinstance(value, Version):
                    return value
                try:
                    return Version.coerce(string(value))
                except ValueError:
                    SlimLogger.error("Expected version string, not ", value)
            return (
                self._source.version
            )  # cracks the source package and extracts its version number

        input_groups = app_info.inputGroups

        self._input_groups = OrderedDict(
            (name, set(input_groups[name])) for name in input_groups
        )
        self._dependencies = OrderedDict(
            (app_id, None) for app_id in app_info.dependencies
        )
        if hasattr(app_info, "optional_dependencies"):
            self._optional_dependencies = OrderedDict(
                (app_id, None) for app_id in app_info.optional_dependencies
            )
        else:
            self._optional_dependencies = {}
        self._dependents = OrderedDict((app_id, None) for app_id in app_info.dependents)
        self._is_external = app_info.get("is_external", False)
        self._is_root = app_info.get("is_root", False)
        self._source = source()
        self._version = version()

        self._server_class = server_class
        self._deployment_package = None
        self._version_range = []

    # region Special methods

    def __repr__(self):
        return repr(self.source.package)

    def __str__(self):
        return _encode(self.to_dict())

    # endregion

    # region Properties

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def optional_dependencies(self):
        return self._optional_dependencies

    @property
    def dependents(self):
        return self._dependents

    @property
    def deployment_package(self):
        return self._deployment_package

    @property
    def input_groups(self):
        return self._input_groups

    @input_groups.setter
    def input_groups(self, value):
        self._input_groups = value

    @property
    def id(self):  # pylint: disable=invalid-name
        return self._source.id

    @property
    def is_external(self):
        return self._is_external

    @property
    def is_root(self):
        return self._is_root

    @property
    def qualified_id(self):
        return self._source.qualified_id

    @property
    def source(self):
        return self._source

    @property
    def version(self):
        return self._version

    @property
    def version_range(self):
        return self._version_range

    # endregion

    # region Methods

    def add_dependency_placeholder(self, app_id):
        self.dependencies[app_id] = None

    def add_dependent_placeholder(self, app_id):
        self.dependents[app_id] = None

    def create_deployment_package(self):

        input_groups = (
            list(self._input_groups.keys()) if len(self._input_groups) > 0 else None
        )
        server_class = self._server_class

        deployment_specification = AppDeploymentSpecification(
            (("name", server_class.name), ("workload", server_class.workload))
            if input_groups is None
            else (
                ("name", server_class.name),
                ("workload", server_class.workload),
                ("inputGroups", input_groups),
            )
        )

        self._deployment_package = AppDeploymentPackage(
            self.source, deployment_specification
        )

    @classmethod
    def from_app_source(cls, app_source, app_dependents, server_class, target_os):
        package = server_class.add_source(app_source.package)
        dependencies = []
        optional_dependencies = []

        if app_source.manifest.dependencies:
            # Perform filtering for target_os if needed
            all_dependencies = list(
                app_source.get_dependencies_for_target_os(target_os)
            )

            dependencies = [
                app_id for app_id, app in all_dependencies if app.optional is False
            ]

            optional_dependencies = [
                app_id for app_id, app in all_dependencies if app.optional is True
            ]

        dependents = (
            []
            if app_dependents is None
            else [dependent.id for _, dependent in app_dependents]
        )
        app_info = ObjectView(
            (
                ("dependencies", dependencies),
                ("optional_dependencies", optional_dependencies),
                ("dependents", dependents),
                ("inputGroups", {}),
                ("source", package),
            )
        )
        return AppInstallation(server_class, app_info)

    def get_version_conflicts(self, dependents):

        if dependents is None:
            return []

        version = Version.coerce(self.version)
        conflicts = []

        for dependent, version_range in dependents.items():
            if not version_range.match(version):
                conflicts.append((dependent, version_range))

        return conflicts

    def merge_input_groups(self, other):

        input_groups = self._input_groups

        for name, other_aids in other.input_groups.items():
            self_aids = input_groups.get(name)
            input_groups[name] = (
                set(other_aids) if self_aids is None else self_aids.union(other_aids)
            )

    def partition(self, output_dir):
        if self._deployment_package is None:
            self.create_deployment_package()
        if self._deployment_package.is_empty:
            return None
        return self._deployment_package.export(output_dir)

    def reset_version_range(self):
        version_range = []
        app_id = self.id

        for dependent in self.dependents.values():
            version_range.append(string(dependent.dependencies[app_id].version_range))

        self._version_range = semantic_version.Spec(*version_range)

    def resolve_dependencies(self, graph):

        dependencies = self._dependencies

        for name in self._dependencies:
            try:
                installation = graph[name]
            except KeyError:
                SlimLogger.error(
                    "Cannot resolve dependency for app ",
                    encode_string(self.qualified_id),
                    ": ",
                    name,
                )
            else:
                dependencies[name] = AppInstallationDependency(self, installation)

    def resolve_dependents(self, graph):

        dependents = self._dependents
        version_range = []

        for name in dependents:
            try:
                installation = graph[name]
            except KeyError:
                SlimLogger.error(
                    "Cannot resolve dependency on app ",
                    encode_string(self.id),
                    ": ",
                    name,
                )
            else:
                try:
                    dependency = installation.dependencies[self.id]
                except KeyError:
                    pass
                else:
                    version_range.append(string(dependency.version_range))
                dependents[name] = installation

        self._version_range = semantic_version.Spec(*version_range)

        if not self._version_range.match(self._version):
            SlimLogger.error(
                "Invalid dependency ",
                self.id,
                ":",
                self._version,
                " is outside of required version range(s): ",
                string(self._version_range),
            )

    def to_dict(self):
        return OrderedDict(
            (
                ("dependencies", list(self.dependencies.keys())),
                ("optional_dependencies", list(self.optional_dependencies.keys())),
                ("dependents", list(self.dependents.keys())),
                ("is_external", self._is_external),
                ("is_root", self._is_root),
                (
                    "inputGroups",
                    OrderedDict(
                        (fg, sorted(aids))
                        for fg, aids in sorted(self.input_groups.items())
                        if len(aids) > 0
                    ),
                ),
                ("source", path.basename(self._source.package)),
                ("version", string(self._version)),
            )
        )

    def update_input_groups(self, app_id, input_groups):
        """Updates the input groups for this installation based on the `input_groups` required by `app_id`.

        :param app_id:
        :type app_id: string

        :param deployment_specification:
        :
        :return: :const:`None`.

        """

        # Remove unnecessary input groups

        remove_list = []

        for name in self.input_groups:
            app_ids = self.input_groups[name]
            if app_id in app_ids and name not in input_groups:
                app_ids.remove(app_id)
                if len(app_ids) == 0:
                    remove_list.append(name)

        for name in remove_list:
            del self.input_groups[name]

        # Ensure all input groups for app_id are represented

        if input_groups is not None:

            for name in input_groups:
                app_ids = self.input_groups.get(name, set())
                app_ids.add(app_id)
                self.input_groups[name] = app_ids

    # endregion
    pass  # pylint: disable=unnecessary-pass


class AppInstallationAction(ObjectView):

    # pylint: disable=no-member
    def __init__(self, value):

        try:
            ObjectView.__init__(self, value)
        except ValueError:
            raise ValueError("Poorly formed installation action: " + value)

        self._validate_field_names(
            "installation action", AppInstallationAction._field_names
        )

        if (
            self.action == SlimInstallationGraphActions.remove
        ):  # pylint: disable=no-else-return
            if "app_id" not in self.args or not self.args.app_id:
                raise ValueError("Expected an app id along with the " + self.action)
            return
        elif self.action in [
            SlimInstallationGraphActions.add,
            SlimInstallationGraphActions.set,
        ]:
            if "app_package" not in self.args or not self.args.app_package:
                raise ValueError(
                    "Expected an app package along with the " + self.action
                )
            if "combine_search_head_indexer_workloads" not in self.args:
                self.args["combine_search_head_indexer_workloads"] = 0
            if "workloads" not in self.args:
                self.args["workloads"] = None
            return
        elif self.action == SlimInstallationGraphActions.update:
            if "app_package" not in self.args:
                raise ValueError(
                    "Expected an app package along with the update action: "
                    + self.action
                )
            return

        raise ValueError(
            "Installation action "
            + encode_string(self.action)
            + " is unknown or not-yet-implemented"
        )

    _field_names = frozenset(("action", "args"))


class AppInstallationDependency(object):
    def __init__(self, installation, dependency):
        self._version_range = installation.source.manifest.dependencies[
            dependency.id
        ].version
        self._dependencies = dependency.dependencies
        self._optional_dependencies = dependency.optional_dependencies
        self._dependents = dependency.dependents
        self._version = dependency.version
        self._installation = dependency

    def __repr__(self):
        value = (
            "AppInstallationDependency(installation="
            + repr(self._installation.id)
            + ", version="
            + repr(self._version)
            + ", version_range="
            + repr(self._version_range)
            + ")"
        )
        return value

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def optional_dependencies(self):
        return self._optional_dependencies

    @property
    def dependents(self):
        return self._dependents

    @property
    def installation(self):
        return self._installation

    @property
    def version(self):
        return self._version

    @property
    def version_range(self):
        return self._version_range


class AppInstallationGraph(Mapping):
    """A directed acyclic graph representing the installation of a set of apps on a server class"""

    def __init__(self, server_class, object_view):

        self._graph = graph = OrderedDict()
        self._server_class = server_class

        for name, info in object_view.items():
            installation = AppInstallation(server_class, info)
            if installation.id != name:
                SlimLogger.error(
                    "Expected source for ",
                    name,
                    ", not ",
                    installation.id,
                    ": ",
                    _encode(info),
                )
                continue  # Keep going to discover and report other errors of this type
            graph[name] = installation

        self._resolve()

    # region Special methods

    def __getitem__(self, app_id):
        return self._graph.__getitem__(app_id)

    def __contains__(self, app_id):
        return self._graph.__contains__(app_id)

    def __setitem__(self, key, value):
        return self._graph.__setitem__(key, value)

    def __iter__(self):
        return self._graph.__iter__()

    def __len__(self):
        return self._graph.__len__()

    def __repr__(self):
        value = (
            "AppInstallationGraph("
            + repr(self._server_class)
            + ", ["
            + ", ".join((repr(installation) for installation in self._graph))
            + "])"
        )
        return value

    def __str__(self):
        _encode(self.to_dict())

    # endregion

    # region Properties

    @property
    def server_class(self):
        return self._server_class

    # endregion

    # region Methods

    def add_installation(self, installation):
        """Add installation to the current app installation graph

        The installation is added using an iterative breadth first merge algorithm.

        """
        queue = deque((installation,))
        graph = self._graph

        while len(queue) > 0:
            installation = queue.pop()
            if installation.id not in graph:
                graph[installation.id] = installation
                queue.extendleft(
                    (
                        dependency.installation
                        for dependency in installation.dependencies.values()
                    )
                )

    # TODO: SPL-120441: Document dependency resolution rules implemented by AppInstallationGraph.from_dependency_graph
    # pylint: disable=protected-access
    # pylint: disable=too-many-arguments
    # noinspection PyProtectedMember
    @classmethod
    def from_dependency_graph(
        cls, server_class, dependency_graph, target_os, validate=True, is_external=False
    ):
        """Constructs an installation graph from a dependency graph.

        The installation graph created is based on the given server class's installation graph.

        :param server_class:
        :type server_class: AppServerClass

        :param dependency_graph:
        :type dependency_graph: AppDependencyGraph

        :param target_os: if not None, only use dependencies for the given target OS
        :type target_os: string

        :return: A new installation graph.
        :rtype: AppInstallationGraph

        """
        root = dependency_graph.root
        installation = server_class.apps.get(root.id)
        installation_graph = AppInstallationGraph(server_class, ObjectView.empty)

        if installation is not None:

            # The root app in dependency_graph is now a root app in the installation graph that we're constructing
            # It is marked as an external app--that is an app that is unmanaged by the DMC--if is_external is True

            installation._is_external = is_external
            installation._is_root = True

            # The app represented by dependency_graph is installed

            if root.version == installation.version:
                installation_graph.add_installation(
                    installation
                )  # no change in version
                return installation_graph

            # The app represented by dependency_graph is being updated; either downgraded or upgraded (each are allowed)

            if validate and not installation.version_range.match(root.version):
                # The app represented by dependency_graph conflicts with the current installation
                SlimLogger.error(
                    "Cannot install ",
                    root.qualified_id,
                    " to ",
                    server_class.apps.server_class.name,
                    " because " "its version number does not match ",
                    installation.version_range,
                    " as required by the " "installation",
                )
                slim_configuration.payload.status = SlimStatus.STATUS_ERROR_CONFLICT
                return installation_graph  # add nothing to the graph

        def visit(app_source, app_dependencies, app_dependents):

            if app_source is root:
                is_root = True
                is_external_visit = is_external
            else:
                try:
                    installed = server_class.apps[app_source.id]
                    dependencies = installed.dependencies.values()
                except KeyError:
                    is_root = False
                    is_external_visit = False
                else:
                    version = semantic_version.Spec(
                        *(
                            string(dependency.version)
                            for dependency, _ in app_dependents
                        )
                    )
                    if version.match(installed.version):
                        # Keep the installed version, including its dependencies which will now drive graph traversal
                        app_dependencies = OrderedSet(
                            (d.installation.source for d in dependencies)
                        )
                        app_source = installed.source
                    elif validate and not installed.version_range.match(
                        app_source.version
                    ):
                        # Report a version conflict
                        SlimLogger.error(
                            "Cannot install ",
                            app_source.qualified_id,
                            " to server class ",
                            server_class.name,
                            " because a version in this range is required by the installation: ",
                            installed.version_range,
                        )
                        slim_configuration.payload.status = (
                            SlimStatus.STATUS_ERROR_CONFLICT
                        )
                        return OrderedSet()
                    is_root = installed.is_root
                    is_external_visit = installed.is_external

            app_installation = AppInstallation.from_app_source(
                app_source, app_dependents, server_class, target_os
            )
            installation_graph[app_source.id] = app_installation
            app_installation._is_root = is_root
            app_installation._is_external = is_external_visit

            return app_dependencies

        dependency_graph.traverse(visit)

        # If any optional dependency is installed, add it to the dependencies field of the root app
        # This is only for the installation graph of the app being added
        for app in installation_graph.values():
            for optional_dependency in app.optional_dependencies:
                if optional_dependency in installation_graph:
                    app.add_dependency_placeholder(optional_dependency)

        installation_graph._resolve()

        return installation_graph

    # pylint: enable=too-many-arguments

    def is_cyclic(self):
        """Returns True if this dependency graph is cyclic."""
        graph = self._graph
        graph_path = set()
        visited = set()

        def visit(app_id, installation):
            if app_id in visited:
                return False
            visited.add(app_id)
            graph_path.add(app_id)
            for dependency_id, dependency in installation.dependencies.items():
                if dependency_id in graph_path:
                    return True
                if dependency is None:
                    continue  # unresolved dependency
                if visit(dependency_id, dependency.installation):
                    return True
            graph_path.remove(app_id)
            return False

        return any(
            visit(app_id, installation) for app_id, installation in graph.items()
        )

    def to_dict(self):
        return OrderedDict(
            (
                (app_id, installation.to_dict())
                for app_id, installation in self._graph.items()
            )
        )

    def remove_installation(self, installation):
        """Remove an app installation from the current installation graph

        The app is removed using an iterative breadth first merge algorithm.

        """
        queue = deque((installation,))
        root = installation.id

        graph = self._graph
        graph_updates = OrderedDict(
            (
                (SlimInstallationGraphActions.add, []),
                (SlimInstallationGraphActions.update, {}),
                (SlimInstallationGraphActions.remove, []),
            )
        )

        while len(queue) > 0:
            installation = queue.pop()
            app_id = installation.id

            for dependency in installation.dependencies.values():
                dependency = dependency.installation
                del dependency.dependents[app_id]
                input_groups = dependency.input_groups

                for input_group in input_groups:
                    app_ids = input_groups[input_group]
                    try:
                        app_ids.remove(root)
                    except KeyError:
                        pass

                queue.appendleft(dependency)

            if len(installation.dependents) == 0:
                if app_id is root or not installation.is_root:
                    # Remove the app because:
                    # * its reference count dropped to zero
                    # * it's either the app that's being uninstalled or an app dependency that's not rooted
                    # A rooted app dependency represents a dependency that was installed independently of any app that
                    # depends on it.
                    if app_id in graph:
                        assert (
                            app_id
                            not in graph_updates[SlimInstallationGraphActions.remove]
                        )
                        graph_updates[SlimInstallationGraphActions.remove].append(
                            app_id
                        )
                        del graph[app_id]
            else:
                # Reset the app's version range because its reference count has not yet and might never drop to zero
                installation.reset_version_range()

        slim_configuration.payload.add_graph_update(
            self.server_class.name, updates=graph_updates
        )

    def describe_installation(self, installation):
        """Describe an app within the current app installation graph

        This is a readonly operation to describe the installations for the app

        """
        queue = deque((installation,))
        graph = self._graph

        installations = OrderedDict()

        while len(queue) > 0:
            installation = queue.pop()

            app_id = installation.id
            installations[app_id] = installation

            for dependency in installation.dependencies.values():
                dependency = dependency.installation
                installations[dependency.id] = dependency
                queue.appendleft(dependency)

        installations = (
            None
            if len(installations) == 0
            else OrderedSet(
                (
                    installation
                    for app_id, installation in installations.items()
                    if app_id in graph
                )
            )
        )

        return installations

    # TODO: SPL-120377: Ensure AppInstallationGraph.update works under Python 3.x
    # Python 3.x implements the Mapping.items method as a view over a Mapping. Hence, a Mapping cannot be updated while
    # iterating over its items. The task here is to ensure that this method works under Python 3.x given that we're
    # updating Mapping objects that we may be iterating over.
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    def update(self, app_installation_graph, disable_automatic_resolution=False):
        """Updates the current installation graph with elements from another app installation graph

        :param app_installation_graph: an :class:`AppInstallationGraph` that was produced by a call to
        :meth:`AppInstallation.from_dependency_graph`.
        :type app_installation_graph: AppInstallationGraph

        :param disable_automatic_resolution:
        :type disable_automatic_resolution: bool

        :return: :const:`None`.

        """
        graph = self._graph
        graph_updates = OrderedDict(
            (
                (SlimInstallationGraphActions.add, []),
                (SlimInstallationGraphActions.update, OrderedDict()),
                (SlimInstallationGraphActions.remove, []),
            )
        )

        for aid in app_installation_graph:

            updated = app_installation_graph[aid]

            # Verify that the updated app is compatible with all apps in the current installation graph and vice versa

            incompatible_apps = updated.source.manifest.incompatibleApps

            # ..first verify that the installation is compatible with the app

            if incompatible_apps:
                for incompatible_aid in incompatible_apps:
                    try:
                        installed = graph[incompatible_aid]
                    except KeyError:
                        pass
                    else:
                        version_spec = incompatible_apps[incompatible_aid]
                        if version_spec.match(installed.version):
                            SlimLogger.error(
                                "Installed app ",
                                installed.qualified_id,
                                " is incompatible with ",
                                updated.qualified_id,
                            )
                            slim_configuration.payload.status = (
                                SlimStatus.STATUS_ERROR_CONFLICT
                            )

            # ..then verify that the app is compatible with the installation

            # TODO: consider optimizing this loop (e.g., by computing the set of apps that are incompatible with
            # the installation once; prior to entering this loop)

            for installed_aid in graph:
                installed = graph[installed_aid]
                incompatible_apps = installed.source.manifest.incompatibleApps
                if incompatible_apps is None:
                    continue
                try:
                    version_spec = incompatible_apps[aid]
                except KeyError:
                    continue
                if version_spec.match(updated.version):
                    SlimLogger.error(
                        updated.qualified_id,
                        " is incompatible with installed app ",
                        installed.qualified_id,
                    )
                    slim_configuration.payload.status = SlimStatus.STATUS_ERROR_CONFLICT

            # If optional dependency is installed, add it to the dependencies field of the root app
            # This is for the current overall installation graph
            for installed_aid in graph:
                installed = graph[installed_aid]
                if aid in installed.optional_dependencies:
                    # set both dependencies and dependents links
                    installed.dependencies[aid] = AppInstallationDependency(
                        installed, app_installation_graph[aid]
                    )
                    app_installation_graph[aid].add_dependent_placeholder(installed_aid)

            # Update the current graph with the updated app

            installed = graph.get(aid)

            if installed is None:
                graph[aid] = updated
                graph_updates[SlimInstallationGraphActions.add].append(aid)
                continue

            # ..ensure correctness of each dependency's dependent items collection

            for (
                dependency_id,
                dependency_installation,
            ) in installed.dependencies.items():
                if dependency_id not in updated.dependencies:
                    # Remove the link to this app from a dependency that no longer exists
                    del dependency_installation.dependents[aid]

            for dependency_id, dependency_installation in updated.dependencies.items():
                if dependency_id not in installed.dependencies:
                    # Add a link to this app from a dependency that now exists
                    dependency_installation.dependents[aid] = dependency_installation

            # ..ensure that the updated.dependents dictionary includes all items from installed.dependents

            for dependent_id in installed.dependents:
                if dependent_id in app_installation_graph:
                    updated.dependents[dependent_id] = app_installation_graph[
                        dependent_id
                    ]
                else:
                    updated.dependents[dependent_id] = graph[dependent_id]

            updated.merge_input_groups(installed)

            # Record whether this app has had a package update, and make sure we are allowed to do this
            # automatically (disable_automatic_resolution = False)
            if path.basename(installed.source.package) != path.basename(
                updated.source.package
            ):
                if disable_automatic_resolution:
                    SlimLogger.error(
                        installed.qualified_id,
                        " needs to be updated to ",
                        updated.qualified_id,
                        " to resolve dependency conflicts, but automatic dependency resolution is disabled",
                    )
                    slim_configuration.payload.status = (
                        SlimStatus.STATUS_ERROR_RESOLVABLE_CONFLICT
                    )

                graph_updates[SlimInstallationGraphActions.update][aid] = path.basename(
                    updated.source.package
                )

            graph[aid] = updated

        slim_configuration.payload.add_graph_update(
            self.server_class.name, updates=graph_updates
        )

    # endregion

    # region Privates

    def _resolve(self):
        graph = self._graph

        for name in graph:
            installation = graph[name]
            installation.resolve_dependencies(self)

        for name in graph:
            installation = graph[name]
            installation.resolve_dependents(self)

        if self.is_cyclic():
            SlimLogger.error("Installation graph is cyclic")

    # endregion
    pass  # pylint: disable=unnecessary-pass
