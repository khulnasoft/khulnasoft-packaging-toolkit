# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import object
from imp import find_module, load_module
from inspect import getmembers, isclass
from os import path

from .. utils import SlimLogger, encode_filename, encode_series, slim_configuration


class AppConfigurationValidationPlugin(object):

    def fix_up(self, stanza, placement, position):
        declarations = stanza.setting_declarations
        try:
            disabled = declarations['disabled']
        except KeyError:
            from ._configuration_spec import AppConfigurationSettingDeclaration  # nopep8, pylint: disable=import-outside-toplevel
            disabled = AppConfigurationSettingDeclaration.Section('disabled', '<bool>', placement, position)
            declarations['disabled'] = disabled
        else:
            disabled._placement = placement  # pylint: disable=protected-access

    @staticmethod
    def get(configuration, app_root):  # pylint: disable=inconsistent-return-statements
        """ Returns the app configuration validation plugin for the named configuration object.

        The search for a plugin proceeds from `{app_root}/README` to `{slim_home}/config/conf-specs`. If no specific
        plugin is found, the default plugin represented by this class is returned. The default plugin ensures that
        the `disabled` setting is added to each stanza in the named `configuration`.

        :param configuration: Configuration object name.
        :type configuration: string

        :param app_root: App root directory name.
        :type app_root: string

        :return: app configuration validation plugin for the named configuration object.
        :rtype: AppConfigurationValidationPlugin

        """
        cls = AppConfigurationValidationPlugin  # pylint: disable=inconsistent-return-statements

        try:
            plugin = cls._instances[configuration]  # pylint: disable=protected-access

        except KeyError:
            plugin_path = [path.join(app_root, 'README'), slim_configuration.configuration_spec_path]

            try:
                result = find_module(configuration, plugin_path)

            except ImportError:
                plugin = cls._default  # pylint: disable=protected-access

            else:
                plugin_name = 'slim.app.configuration_validation_plugin.' + configuration
                file, path_name, description = result  # pylint: disable=redefined-builtin

                with file:
                    try:
                        plugin_module = load_module(plugin_name, file, path_name, description)
                    except ImportError as error:
                        SlimLogger.fatal(
                            'Could not load ', plugin_name, ' from ', encode_filename(path_name), ': ', error
                        )
                        return  # SlimLogger.fatal does not return, but this quiets pylint

                def predicate(member):
                    return isclass(member) and issubclass(member, cls) and member.__module__ == plugin_name

                plugins = getmembers(plugin_module, predicate)

                if len(plugins) == 0:
                    SlimLogger.fatal(
                        'Expected to find an AppConfigurationValidation-derived class in ', plugin_name, ' at ',
                        encode_filename(path_name)
                    )
                    return  # SlimLogger.fatal does not return, but this quiets pylint

                if len(plugins) >= 2:
                    SlimLogger.fatal(
                        'Expected to find a single AppConfigurationValidation-derived class in ', plugin_name, ' at ',
                        encode_filename(path_name), ', not ', len(plugins), ': ',
                        encode_series(plugin[0] for plugin in plugins)
                    )
                    return  # SlimLogger.fatal does not return, but this quiets pylint

                plugin_class = plugins[0][1]
                plugin = plugin_class()

            AppConfigurationValidationPlugin._instances[configuration] = plugin

        return plugin

    _instances = dict()
    _default = None

AppConfigurationValidationPlugin._default = AppConfigurationValidationPlugin()  # pylint: disable=protected-access
