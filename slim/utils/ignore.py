#!/usr/bin/env python
# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import object
from collections import Iterable, OrderedDict  # pylint: disable=no-name-in-module
from os import path

import fnmatch
import io
import re

from . _configuration import slim_configuration
from . _encoders import encode_filename
from . logger import *
from . internal import string


__all__ = ['SlimIgnore']


class SlimIgnore(object):

    def __init__(self, app_name, source_directory):

        excludes, includes = SlimIgnore._parse_patterns(source_directory)
        excludes = SlimIgnore._compile_patterns(excludes)

        if len(includes) == 0:
            def _filter(item):
                value = None if SlimIgnore.Item(self, item).match(excludes) is True else item
                return value
        else:
            includes = SlimIgnore._compile_patterns(includes)

            def _filter(item):
                ignore_item = SlimIgnore.Item(self, item)
                if ignore_item.match(excludes) is False:
                    return item
                if ignore_item.match(includes) is True:
                    return item
                return None

        self._source_pathname = path.normcase(path.abspath(app_name))
        self._source_basename = path.basename(self._source_pathname)
        self._filter = _filter

    # region Methods

    def filter(self, item):
        return self._filter(item)

    def ifilter(self, iterable):
        assert isinstance(iterable, Iterable)
        for item in iterable:
            if self._filter(item) is None:
                continue
            yield item

    # endregion

    # region Protected

    _backslash_quoted_characters = re.compile(r'\\(.)')
    _trailing_spaces = re.compile(r'\\ +\n?$')
    _wildcard = re.compile(r'\.\*')
    _path_sep = '\\' + path.sep
    _escaped_path_sep = _path_sep.replace('\\', '\\\\')

    @staticmethod
    def _compile_patterns(ordered_dict):
        pattern = '|'.join('(?P<' + t + string(n) + '>' + p + ')' for n, (p, t) in enumerate(ordered_dict.items()))
        return re.compile(pattern, re.M | re.S | re.U)

    @staticmethod
    def _strip_regex(rgx):
        # ?m - match multiline
        # ?s - equivalent to 'dot' or 'match all' except new line
        # \Z - match only end of string
        if rgx.endswith('(?ms)'):
            rgx = rgx[:-5]
        if rgx.endswith('\\Z'):
            rgx = rgx[:-2]
        if rgx.startswith('(?s:') and rgx.endswith(')'):
            rgx = rgx[4:-1]
        return rgx

    @staticmethod
    def _parse_patterns(source_directory):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements

        escaped_path_sep = SlimIgnore._escaped_path_sep
        path_sep = SlimIgnore._path_sep
        translate = fnmatch.translate
        excludes = OrderedDict()
        includes = OrderedDict()
        for line in SlimIgnore._read_lines(source_directory):
            line, subn = SlimIgnore._trailing_spaces.subn(r' ', line)

            if subn == 0:
                line = line.rstrip()

            line = SlimIgnore._backslash_quoted_characters.sub(r'\1', line)

            if not line.startswith('!'):
                target = excludes
            elif len(line) > 1:
                target = includes
                line = line[1:]
            else:
                continue  # blank line

            if line.endswith('/**'):
                line = line[:-2]

            if not line.endswith('/'):
                pattern_type = 'f'
            elif len(line) > 1:
                pattern_type = 'd'
                line = line[:-1]
            else:
                continue  # blank line

            names = path.normcase(path.normpath(line)).split(path.sep)
            first_name = names[0]
            if len(names) == 1:
                unparsed_name = translate(first_name)
                parsed_name = SlimIgnore._strip_regex(unparsed_name)
                # Pattern matches an unanchored file or directory node name (e.g., 'foo' or 'ba*r')
                pattern = r'(?:.*' + path_sep + ')?' + parsed_name
            else:
                # Pattern matches an anchored or unanchored path segment
                # anchored patterns start with '/' (e.g., '/foo*/bar')
                # unanchored patterns start with '**/' or a node name (e.g., '**/foo/ba*r' or 'foo/ba*r')
                start = 1 if len(first_name) == 0 or first_name == '**' else 0

                for i, name in enumerate(names[start:], start):
                    # We trim the trailing seven unnecessary characters produced by fnmatch.translate: r'(?ms)\Z'
                    unparsed_name = translate(name)
                    name = SlimIgnore._strip_regex(unparsed_name)
                    if name == '**':
                        names[i] = '.*'
                    else:
                        names[i] = SlimIgnore._wildcard.sub(r'[^' + escaped_path_sep + ']*', name)

                pattern = path_sep.join(names[start:]) + r'\Z'

                if first_name == '**':  # TODO: Should the comparison not be len(first_name) == 0 or first_name == '**'
                    pattern = r'(?:.*' + path_sep + ')?' + pattern

            try:
                current_pattern_type = target[pattern]
            except KeyError:
                target[pattern] = pattern_type
            else:
                if pattern_type == 'f' and current_pattern_type == 'd':
                    del target[pattern]     # remove the currently-defined pattern from our targeted dictionary
                    target[pattern] = pattern_type  # add the new pattern to the end of our targeted dictionary

        excludes[r'\.slimignore\Z'] = 'f'
        # excludes[path_sep + r'\.slimignore\Z'] = 'f'
        return excludes, includes

    @staticmethod
    def _read_lines(source_directory):
        for slimignore_file in (
                path.join(source_directory, '.slimignore'),
                path.join(slim_configuration.user_config, 'ignore'),
                path.join(slim_configuration.system_config, 'ignore')):
            try:
                with io.open(slimignore_file, encoding='utf-8') as istream:
                    for line in istream:
                        line = line.lstrip()
                        if len(line) == 0 or line.startswith('#'):
                            continue  # blank- or comment-line
                        yield line
            except IOError as error:
                if error.errno != 2:  # no such file
                    SlimLogger.fatal('Could not open ', encode_filename(slimignore_file), ': ', error)

    # endregion

    class Item(object):

        def __init__(self, slim_ignore, item):

            self._underlying_item = item
            item_type = type(item)

            if item_type is string:
                # NOTE: We break from gitignore semantics by using path.isdir. It returns True for symbolic links to
                # directories. We do this because we follow links when creating source packages; replacing symbolic
                # links with the content of the link target.
                self._isdir = path.isdir
                name = path.normcase(path.abspath(item))
                source_pathname = slim_ignore._source_pathname  # pylint: disable=protected-access
                common_prefix = path.commonprefix([source_pathname, name])
                self._name = path.normcase(None if len(common_prefix) == len(name) else name[len(common_prefix) + 1:])
            else:
                # Expectation: We've got a TarInfo object. That said, we'll accept any object with name and isdir attrs
                self._isdir = item_type.isdir
                name = path.normcase(item.name)
                source_basename = slim_ignore._source_basename  # pylint: disable=protected-access
                common_prefix = path.commonprefix([source_basename, name])
                self._name = None if len(common_prefix) == len(name) else name[len(common_prefix) + 1:]

        def __str__(self):
            return self._name

        def match(self, pattern):
            if self._name is None:
                # Expectation: this is the source root directory name (see Item.__init__)
                return False
            match = pattern.match(self._name)
            if match is None:
                return False
            group = match.lastgroup
            if group[0] == 'd':
                if not self._isdir(self._underlying_item):
                    return False
            return True
