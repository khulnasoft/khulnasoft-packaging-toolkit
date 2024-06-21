#!/usr/bin/env python
# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import object
from collections import OrderedDict
from tempfile import gettempdir
from os import environ, path
import os
import sys
import errno

try:
    # noinspection PyCompatibility
    from configparser import RawConfigParser, SafeConfigParser
    import configparser
except ImportError:
    # noinspection PyCompatibility
    from ConfigParser import RawConfigParser, SafeConfigParser
    # noinspection PyPep8Naming
    import ConfigParser as configparser

import io
import logging

from . _encoders import encode_series

from . logger import SlimLogger
from . internal import string
from . payload import SlimPayload
from . public import SlimCacheInfo


__all__ = ['slim_configuration']


class SlimConfigurationManager(object):

    def __init__(self):

        self._cache = None
        self._configuration_spec_path = None
        self._output_dir = None
        self._payload = None
        self._repository_path = None
        self._settings = None
        self._temp_directory_path = None
        self._sanitized_paths = None

    # region Properties

    @property
    def sanitized_paths(self):
        paths = [
            (os.path.join(self.home, ''), 'slim/'),
            (os.path.join(self.cache.cache_path, ''), ''),
        ]
        if self._sanitized_paths:
            paths += self._sanitized_paths
        return paths

    @sanitized_paths.setter
    def sanitized_paths(self, value):
        self._sanitized_paths = value

    @property
    def cache(self):
        value = self._cache
        if value is None:
            value = self._cache = SlimCacheInfo(self.temp_directory_path)
        return value

    @property
    def configuration_spec_path(self):
        return self._get_path_option('_configuration_spec_path', 'configuration_spec_path')

    @configuration_spec_path.setter
    def configuration_spec_path(self, value):
        self._settings.set('option', 'configuration_spec_path', value)
        self._configuration_spec_path = None

    @property
    def home(self):
        return self._slim_home

    @property
    def output_dir(self):
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value):
        self._output_dir = value

    @property
    def payload(self):
        return self._payload

    @property
    def repository_path(self):
        return self._get_path_option('_repository_path', 'repository_path')

    @repository_path.setter
    def repository_path(self, value):
        self._settings.set('option', 'repository_path', value)
        self._repository_path = None

    @property
    def system_config(self):
        return SlimConfigurationManager._slim_config

    @property
    def temp_directory_path(self):
        return self._get_path_option('_temp_directory_path', 'temp_directory_path')

    @property
    def user_config(self):
        return SlimConfigurationManager._user_config

    # endregion

    # region Methods

    # pylint: disable=protected-access
    @staticmethod
    def get(setting_names, location=None, validate=False):

        cls = SlimConfigurationManager
        files = list(cls._files.values()) if location is None else [cls._files[location]]  # nopep8, pylint: disable=unsubscriptable-object

        parser = cls._create_config_parser(RawConfigParser, files, validate)
        settings = OrderedDict()
        undefined_names = []

        def add_all_options(section, options):
            for option in options:
                setting_name = section + '.' + option
                if parser.has_option(section, option):
                    settings[setting_name] = parser.get(section, option)
                    continue
                settings[setting_name] = None

        for setting_name in setting_names:
            if setting_name == '*':
                # Get all options in all sections
                for section, options in cls._defaults.items():
                    if parser.has_section(section):
                        add_all_options(section, options)
                        continue
                    for option in options:
                        setting_name = section + '.' + option
                        settings[setting_name] = None
                continue
            keys = setting_name.split('.', 1)
            if len(keys) == 1 or keys[1] == '*':
                # Get all options in the named section
                section = keys[0]
                try:
                    options = cls._defaults[section]  # pylint: disable=unsubscriptable-object
                except KeyError:
                    undefined_names.append(section)
                else:
                    add_all_options(section, options)
                continue
            section, option = keys
            if section in cls._defaults and option in cls._defaults[section]:  # nopep8, pylint: disable=unsupported-membership-test,unsubscriptable-object
                # Get the named option in the named section
                try:
                    settings[setting_name] = parser.get(section, option)
                except (configparser.NoSectionError, configparser.NoOptionError):
                    settings[setting_name] = None
                continue
            undefined_names.append(setting_name)

        return settings, undefined_names

    def load(self):

        cls = SlimConfigurationManager

        self._cache = None
        self._output_dir = os.getcwd()
        self._payload = SlimPayload()
        self._configuration_spec_path = self._repository_path = self._temp_directory_path = None  # set on first access
        self._settings = SlimConfigurationManager._create_config_parser(SafeConfigParser, list(cls._files.values()))

        SlimLogger.set_level(cls._defaults['logger']['level'])  # pylint: disable=unsubscriptable-object

    @staticmethod
    def set(settings, location=None):

        if location is None:
            location = 'user'

        cls = SlimConfigurationManager

        filename = cls._files[location]  # pylint: disable=unsubscriptable-object
        defaults = cls._defaults
        undefined_names = []

        parser = cls._create_config_parser(RawConfigParser, [filename])

        for setting_name, setting_value in settings.items():
            value = setting_name.split('.', 1)
            if len(value) == 2:
                section, option = value
                if parser.has_section(section) and option in defaults[section]:  # nopep8, pylint: disable=unsubscriptable-object
                    parser.set(section, option, setting_value)
                    continue
            undefined_names.append(setting_name)

        cls._save(parser, filename)
        return undefined_names

    @staticmethod
    def unset(setting_names, location=None):

        if location is None:
            location = 'user'

        cls = SlimConfigurationManager
        filename = cls._files[location]  # pylint: disable=unsubscriptable-object
        parser = cls._create_config_parser(RawConfigParser, [filename])

        undefined_names = []

        for setting_name in setting_names:
            values = setting_name.split('.', 1)
            if len(values) == 2:
                section, option = values
                try:
                    parser.remove_option(section, option)
                except configparser.NoSectionError:
                    undefined_names.append(setting_name)
                continue
            undefined_names.append(setting_name)

        cls._save(parser, filename)
        return undefined_names

    # endregion

    # region Privates

    _defaults = _files = _slim_home = _slim_config = user_home = _user_config = None

    @staticmethod
    def _create_config_parser(config_parser_type, filenames, validate=False):

        parser = config_parser_type(defaults=environ)

        slim_sections = SlimConfigurationManager._defaults
        for name in slim_sections:  # pylint: disable=not-an-iterable
            parser.add_section(name)

        try:
            parser.read(filenames)

            if validate:
                # Report any sections we don't understand
                extra_sections = [
                    section for section in parser.sections() if section not in slim_sections  # nopep8, pylint: disable=unsupported-membership-test
                ]
                if len(extra_sections) > 0:
                    SlimLogger.warning('ignoring unrecognized section names: ', encode_series(extra_sections))

                # Report any options we don't understand for sections we do understand
                default_options = parser.defaults()
                for section, slim_options in SlimConfigurationManager._defaults.items():
                    extra_options = [
                        option for option in parser.options(section)
                        if option not in slim_options and option not in default_options
                    ]
                    if len(extra_options) > 0:
                        SlimLogger.warning('ignoring unrecognized options for section [', section, ']: ',
                                           encode_series(extra_options))

        except configparser.ParsingError as error:
            SlimLogger.warning(error)

        return parser

    def _get(self, section, option):

        try:
            return string(self._settings.get(section, option))
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass

        try:
            return self._defaults[section]  # pylint: disable=unsubscriptable-object
        except KeyError:
            pass

        raise configparser.NoOptionError(option, section)

    def _get_logger(self, option):
        return self._get('logger', option)

    def _get_option(self, option):
        return self._get('option', option)

    def _get_path_option(self, attr, name):

        value = getattr(self, attr)

        if value is None:
            value = path.expanduser(path.normpath(self._get_option(name)))
            try:
                os.makedirs(value)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise
            setattr(self, attr, value)

        return value

    @staticmethod
    def _initialize(system_home=None):
        """ Initializes the SlimConfigurationManager class

        This function is provided for testability. Test authors will typically write code that looks like this:
        .. code-block

            from slim.configuration import SlimConfigurationManager, slim_configuration
            ...

            class SomeTestCase(TestCase):
                ...

                def setUp(self)
                    # modify environment
                    self._real_home = os.environ['HOME']
                    os.environ[str('HOME')] = 'fake/home'
                    ...
                    SlimConfigurationManager._initialize(system_home='fake/slim')
                    ...

                def tearDown(self)
                    # restore environment
                    os.environ[str('HOME')] = self._real_home
                    ...
                    SlimConfigurationManager._initialize()
                    ...

        """
        cls = SlimConfigurationManager

        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            cls._slim_home = path.dirname(string(sys.executable))
        else:
            # Running in a normal Python environment
            cls._slim_home = path.dirname(path.dirname(path.realpath(__file__))) if system_home is None else system_home

        cls._slim_config = path.join(cls._slim_home, 'config')
        cls._user_config = path.expanduser(path.join('~', '.config', 'slim'))

        cls._defaults = OrderedDict((
            ('logger', OrderedDict((
                ('level', logging.getLevelName(logging.STEP)),
            ))),
            ('option', OrderedDict((
                ('configuration_spec_path', path.join(cls._slim_config, 'conf-specs')),
                ('repository_path', path.join(cls._user_config, 'repository')),
                ('temp_directory_path', gettempdir())
            )))
        ))

        cls._files = OrderedDict((
            ('system', path.join(cls._slim_config, 'settings')),
            ('user', path.join(cls._user_config, 'settings'))
        ))

        # We take care to set the SLIM_HOME environment variable using str because Popen under Python 2.7 on Windows
        # does not support unicode environment variable names or values
        environ[str('SLIM_HOME')] = str(cls._slim_home)
        slim_configuration.load()

    @staticmethod
    def _save(parser, filename):

        if not path.isdir(SlimConfigurationManager._user_config):
            os.makedirs(SlimConfigurationManager._user_config)

        with io.open(filename, encoding='utf-8', mode='w', newline='') as stream:
            for section in parser.sections():
                stream.writelines(['[', string(section), ']'])
                for name in SlimConfigurationManager._defaults[section]:  # nopep8, pylint: disable=unsubscriptable-object
                    try:
                        value = parser.get(section, name)
                    except configparser.NoOptionError:
                        continue
                    stream.writelines(['\n', string(name), ' = ', string(value)])
                stream.write('\n\n')
            stream.truncate(stream.tell() - 1)

    # endregion
    pass  # pylint: disable=unnecessary-pass


slim_configuration = SlimConfigurationManager()

# pylint: disable=protected-access
# noinspection PyProtectedMember
SlimConfigurationManager._initialize()
