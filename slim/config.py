#!/usr/bin/env python
# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
import sys

from slim import program
from slim.command import SlimArgumentParser
from slim.utils import SlimLogger, encode_series, slim_configuration

# Argument parser definition

parser = SlimArgumentParser(description='get, set, or unset user or system options')

parser.add_argument_help()

# Command-specific arguments

parser.add_argument(
    '-l', '--location', choices={'system', 'user'}, default=None,
    help='''
        when writing settings: write to the named configuration file (default: user); when reading settings: read only
        from the named configuration file rather than from system and user
    ''',
    metavar='[system|user]')

parser.add_argument(
    '-g', '--get', nargs='*', help='''
        get the values for all settings (using *), all settings in a section (using <section>[.*]), or the named
        settings, where the name of each setting is its section and option name separated by a dot (<section>.<option>)
    ''',
    metavar='<name>'
)

parser.add_argument(
    '-s', '--set', action='append', nargs=2, help='''
        set the value for the named setting, where the name of the setting is its section and option name separated by a
        dot (<section>.<option>)
    ''',
    metavar='<name> <value>'
)

parser.add_argument(
    '-u', '--unset', nargs='*', help='''
        remove the named settings, where the name of each setting is its section and option name separated by a dot
        (<section>.<option>)
    ''',
    metavar='<name>'
)


def main(args):

    location = args.location
    operation_count = 0

    if args.unset is not None:
        undefined_names = slim_configuration.unset(args.unset, location)

        if len(undefined_names) > 0:
            SlimLogger.warning('cannot unset undefined option names: ', encode_series(undefined_names))

        operation_count += 1

    if args.set is not None:

        undefined_names = slim_configuration.set(OrderedDict(args.set), location)

        if len(undefined_names) > 0:
            SlimLogger.warning('cannot set undefined option names: ', encode_series(undefined_names))

        operation_count += 1

    if args.get is not None:

        options, undefined_names = slim_configuration.get(args.get, location, validate=True)

        if len(undefined_names) > 0:
            SlimLogger.warning('cannot get undefined option names: ', encode_series(undefined_names))

        for name, value in list(options.items()):
            if value is None:
                print(name, 'is unset')
                continue
            print(name, '=', value)

        operation_count += 1

    if operation_count == 0:
        parser.prog = program + ' config'
        parser.print_help()


if __name__ == '__main__':
    # noinspection PyBroadException
    try:
        main(parser.parse_args(sys.argv[1:]))
    except SystemExit:
        raise
    except:
        SlimLogger.fatal(exception_info=sys.exc_info())
