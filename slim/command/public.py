# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import object
from argparse import Action, ArgumentError, ArgumentParser

from io import StringIO
import io

from os import path
import os

import sys
import tarfile
import logging

from json.encoder import encode_basestring as encode_string

from .. app import AppDeploymentSpecification, AppInstallationAction
from .. app._internal import ObjectView
from .. utils import SlimLogger, SlimUnreferencedInputGroups, slim_configuration
from .. utils import encode_filename
from .. utils.internal import string
from .. utils.public import SlimTargetOS, SlimTargetOSWildcard

__all__ = [
    'SlimArgumentError',
    'SlimArgumentParser',
    'SlimDeploymentSpecificationArgument',
    'SlimDirectoryArgument',
    'SlimFileArgument',
    'SlimForwarderWorkloadsArgument',
    'SlimInstallationActionArgument',
    'SlimTarballArgument',
    'SlimSourceArgument',
    'SlimStringIOArgument'
]


class SetDebugAction(Action):

    def __init__(self, option_strings, dest, help=None, metavar=None):  # pylint: disable=redefined-builtin
        Action.__init__(self, option_strings, dest, const=True, default=False, help=help, metavar=metavar, nargs=0)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        SlimLogger.set_debug(True)


class SetQuietAction(Action):

    def __init__(self, option_strings, dest, help=None, metavar=None):  # pylint: disable=redefined-builtin
        Action.__init__(self, option_strings, dest, const=True, default=False, help=help, metavar=metavar, nargs=0)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        SlimLogger.set_level(logging.ERROR)


class SetOutputDirAction(Action):

    # pylint: disable=redefined-builtin
    def __init__(self, option_strings, dest, help=None, metavar=None):
        Action.__init__(
            self, option_strings, dest, type=SlimDirectoryArgument(), default=slim_configuration.output_dir, help=help,
            metavar=metavar, nargs=1)

    def __call__(self, parser, namespace, values, option_string=None):
        directory_name = values[0]
        setattr(namespace, self.dest, directory_name)
        slim_configuration.output_dir = directory_name


class SetRepositoryAction(Action):

    # pylint: disable=redefined-builtin
    def __init__(self, option_strings, dest, help=None, metavar=None):
        Action.__init__(
            self, option_strings, dest, type=SlimDirectoryArgument(), default=slim_configuration.repository_path,
            help=help, metavar=metavar, nargs=1
        )

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values[0])
        slim_configuration.repository_path = values[0]


class SlimArgumentError(ArgumentError):

    def __init__(self, *args):
        ArgumentError.__init__(self, argument=None, message=''.join((string(x) for x in args)))


class SlimArgumentParser(ArgumentParser):

    def __init__(self, add_help=False, fromfile_prefix_chars='@', *args, **kwargs):  # nopep8, pylint: disable=keyword-arg-before-vararg

        ArgumentParser.__init__(self, fromfile_prefix_chars=fromfile_prefix_chars, add_help=False, *args, **kwargs)
        self._options = self.add_argument_group(title='options')

        if add_help:
            self.add_help()

        self.register('action', 'set_debug', SetDebugAction)
        self.register('action', 'set_quiet', SetQuietAction)
        self.register('action', 'set_output_dir', SetOutputDirAction)
        self.register('action', 'set_repository', SetRepositoryAction)

    # region Methods

    def add_app_directory(self):
        self._options.add_argument(
            'source', type=SlimDirectoryArgument(existent=True),
            help='location of the app source directory',
            metavar='<app-source>')

    def add_argument(self, *args, **kwargs):
        return self._options.add_argument(*args, **kwargs)

    def add_argument_help(self):
        return self._options.add_argument('-h', '--help', action='help', help='show this help message and exit')

    def add_app_source(self):
        return self._options.add_argument(
            'source', type=SlimSourceArgument(),
            help='location of an app source package or directory',
            metavar='<app-source>')

    def add_app_package(self):
        return self._options.add_argument(
            'source', type=SlimTarballArgument(),
            help='location of an app source package',
            metavar='<app-source>')

    def add_installation(self):
        default_type = SlimStringIOArgument(name='installation.json')
        default = default_type(value='{}')
        return self._options.add_argument(
            '-i', '--installation', type=SlimFileArgument(encoding='utf-8'), default=default,
            help='read installation graph from the file at this location (default: empty).',
            metavar='<filename>')

    def add_output_directory(self, description):
        return self._options.add_argument(
            '-o', '--output-dir', action='set_output_dir',
            help='save ' + description + ' to the directory at this location (default: current directory)',
            metavar='<output-dir>')

    def add_output_file(self, description, manifest=False):
        if manifest:
            return self._options.add_argument(
                '-o', '--output', type=SlimManifestFileArgument('a'), default=SlimManifestFileArgument.default(),
                help='save the ' + description + ' to the file at this location (default: stdout)',
                metavar='<filename>')
        return self._options.add_argument(
            '-o', '--output', type=SlimFileArgument('wb'), default=sys.stdout,
            help='save the ' + description + ' to the file at this location (default: stdout)',
            metavar='<filename>')

    def add_repository(self):
        return self._options.add_argument(
            '-r', '--repository', action='set_repository',
            help='''
                look for dependent source packages in the directory at this location (default:
                ${SLIM_REPOSITORY:=~/.slim/repository})
            ''',
            metavar='<repository>')

    def add_unreferenced_input_groups(self):
        return self._options.add_argument(
            '-u', '--unreferenced-input-groups', type=string,
            choices=frozenset(SlimUnreferencedInputGroups._fields), default=SlimUnreferencedInputGroups.info,
            help='''
                report unreferenced input groups at level: info, warn, or error (default: info)
            ''',
            metavar='<level>')

    def add_combine_search_head_indexer_workloads(self):
        return self._options.add_argument(
            '-c', '--combine-search-head-indexer-workloads',
            action='store_const', const=True, default=False,
            help='combine search head and indexer workloads into a single deployment package')

    def add_forwarder_workloads(self):
        return self._options.add_argument(
            '-f', '--forwarder-workloads',
            type=SlimForwarderWorkloadsArgument(), default=None,
            help='''
                map app input groups to a set of server classes (default: ["_search_heads", "_indexers", "_forwarders"])
            ''',
            metavar='<forwarder-workloads>')

    def add_deployment_packages(self):
        return self._options.add_argument(
            '-d', '--deployment-packages',
            type=SlimDeploymentSpecificationArgument(), nargs='+', default=[],
            help='specify a set of deployment packages by name, workload, and--for forwarder workloads--input groups',
            metavar='<specification>')

    def add_target_os(self):
        return self._options.add_argument(
            '-t', '--target-os',
            type=SlimTargetOSArgument(), default=SlimTargetOSWildcard,
            help='specify a target OS: %s, or %s (default: %s)' % (
                ', '.join(SlimTargetOS[:-1]),
                SlimTargetOS[-1],
                SlimTargetOSWildcard
            ),
            metavar='<target-os>')

    def error(self, message):
        SlimLogger.error(message)
        SlimLogger.exit_on_error()

    # noinspection PyProtectedMember
    @classmethod
    def get(cls, description):
        parser = SlimArgumentParser(description=description)
        return parser

    # endregion
    pass  # pylint: disable=unnecessary-pass


class SlimDeploymentSpecificationArgument(object):  # pylint: disable=redefined-builtin

    def __call__(self, value):
        # TODO: Dnoble: AppDeploymentSpecification writes to SlimLogger which interferes with error handling here
        # In short: We will not always see a ValueError which means that we will frequently return a value when
        # there's an error. This is rooted in the behavior of the json_data module which writes to SlimLogger.
        # Does the JSON schema validator need to accept an error handler argument?
        # See JsonSchema.convert_from.
        try:
            value = AppDeploymentSpecification(string(value.strip()))
        except ValueError as error:
            raise SlimArgumentError(string(error))
        return value


class SlimDirectoryArgument(object):

    def __init__(self, existent=False):
        self._existent = bool(existent)

    def __call__(self, value):
        value = value.strip()
        if not path.isdir(value):
            if self._existent is True:
                raise SlimArgumentError('Directory does not exist: ' + value)
            try:
                os.makedirs(value)
            except OSError as error:
                # Suppress false alarm on error.strerror which is guaranteed to have a string value
                # noinspection PyTypeChecker
                raise SlimArgumentError(
                    'Cannot create directory: ' + error.strerror + ': ' + encode_filename(error.filename))
        return value

    def __repr__(self):
        return 'SlimDirectoryArgument(existent=' + string(self._existent) + ')'


class SlimFileArgument(object):
    """ Factory for creating file object types

    Instances of FileType are typically passed as type= arguments to SlimArgumentParser.add_argument.

    """
    # pylint: disable=too-many-arguments
    def __init__(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        self._mode = mode
        self._buffering = buffering
        self._encoding = encoding
        self._errors = errors
        self._newline = newline

    def __call__(self, value):
        value = value.strip()

        # The special argument "-" means sys.std{in,out}, depending on mode
        if value == '-':
            if 'r' in self._mode:    # pylint: disable=no-else-return
                return sys.stdin
            elif 'w' in self._mode:
                return sys.stdout
            message = 'argument "-" with mode {0}'.format(self._mode)
            raise SlimArgumentError(message)

        # All other arguments are expected to be file names
        try:
            return io.open(value, self._mode, self._buffering, self._encoding, self._errors, self._newline)
        except IOError as error:
            message = 'cannot open {0}: {1}'.format(encode_filename(value), error.strerror)
            raise SlimArgumentError(message)

    def __repr__(self):
        return 'SlimFileArgument(mode={0}, buffering={1}, encoding={2}, errors={3}, newline={4})'.format(
            self._mode, self._buffering, self._encoding, self._errors, self._newline
        )


class SlimManifestFileArgument(SlimFileArgument):
    """ Factory for creating manifest file object types. Manifest files are opened on first access
    """

    # pylint: disable=too-many-arguments
    def __init__(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        SlimFileArgument.__init__(self, mode, buffering, encoding, errors, newline)
        self._ostream = self._value = None
        self._pre_existing = False

    def __call__(self, value):
        # All manifest values are expected to be file names, but opened/created on first access
        self._value = value.strip()
        self._pre_existing = os.path.exists(self._value)
        return self

    def __repr__(self):
        return 'SlimManifestFileArgument(mode={0}, buffering={1}, encoding={2}, errors={3}, newline={4})'.format(
            self._mode, self._buffering, self._encoding, self._errors, self._newline
        )

    @property
    def pre_existing(self):
        return self._pre_existing

    @property
    def ostream(self):
        if not self._ostream:
            self._init_ostream()
        return self._ostream

    @ostream.setter
    def ostream(self, value):
        self._ostream = value

    def _init_ostream(self):
        try:
            self._ostream = io.open(
                self._value, self._mode, self._buffering, self._encoding, self._errors, self._newline
            )
        except IOError as error:
            message = 'cannot open {0}: {1}'.format(encode_filename(self._value), error.strerror)
            raise SlimArgumentError(message)

    @classmethod
    def default(cls):
        arg = SlimManifestFileArgument()
        arg.ostream = sys.stdout
        return arg


class SlimStringIOArgument(object):

    def __init__(self, name):
        self._name = name

    def __call__(self, value):
        try:
            value = StringIO(string(value).strip(), newline=None)
            value.name = self._name
        except ValueError as error:
            raise SlimArgumentError(error)

        return value


class SlimForwarderWorkloadsArgument(object):

    def __call__(self, value):
        value = string(value).strip()
        try:
            forwarder_workloads = ObjectView(value)
        except ValueError as error:
            raise SlimArgumentError('Poorly formed forwarder workloads: ', error, ': ', value)
        return AppDeploymentSpecification.from_forwarder_workloads(forwarder_workloads)


class SlimInstallationActionArgument(object):

    def __call__(self, value):
        try:
            value = AppInstallationAction(string(value).strip())
        except ValueError as error:
            raise SlimArgumentError(error)

        return value


class SlimTarballArgument(object):

    def __call__(self, value):

        value = value.strip()

        try:
            is_tarfile = tarfile.is_tarfile(value)
        except IOError as error:
            raise SlimArgumentError(error.strerror, ': ', value)

        if not is_tarfile:
            raise SlimArgumentError('Expected a tar archive file: ', value)

        return value

    def __repr__(self):
        return 'SlimTarballArgument()'

    @classmethod
    def file_type(cls, tarinfo):
        type_code = tarinfo.type
        try:
            return cls._file_types[type_code]
        except KeyError:
            return 'file of type ' + string(type_code)

    _file_types = {
        b'0': 'regular file',
        b'\0': 'regular file',
        b'1': 'link',
        b'2': 'symbolic link',
        b'3': 'character special device',
        b'4': 'block special device',
        b'5': 'directory',
        b'6': 'FIFO special device',
        b'7': 'contiguous file'
    }


class SlimSourceArgument(object):

    def __call__(self, value):
        try:
            tarball = SlimTarballArgument()
            return tarball(value)
        except SlimArgumentError:
            try:
                directory = SlimDirectoryArgument(existent=True)
                return directory(value)
            except SlimArgumentError:
                raise SlimArgumentError('Expected a source package or source directory name: ', value)

    def __repr__(self):
        return 'SlimSourceArgument()'


class SlimTargetOSArgument(object):

    def __call__(self, value):
        value = string(value).strip()
        if value not in SlimTargetOS:
            raise SlimArgumentError(
                'Expected an OS type, not %s. Valid types are: %s, or %s.' % (
                    encode_string(value),
                    ', '.join(SlimTargetOS[:-1]),
                    SlimTargetOS[-1]))
        return value
