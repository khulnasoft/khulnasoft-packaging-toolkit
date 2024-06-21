#!/usr/bin/env python
# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

# pylint: disable=unused-import
from builtins import next
from os import path
from json.encoder import encode_basestring as encode_string

from .internal import string


def encode_filename(filename):
    """Normalizes and double-quotes a filename

    Quotes within `filename` are backslash-escaped unless the system path separator is a backslash. In this case
    double-quotes within `filename` are converted to a sequence of two double-quotes.

    :param filename: A filename
    :type filename: string

    :return: A quoted filename
    :rtype: string

    """
    return (
        '"'
        + path.normpath(string(filename)).replace(
            '"', '""' if path.sep == "\\" else r"\""
        )
        + '"'
    )


def encode_series(series, coordinator="and"):
    """Joins two or more items in a series

    A comma separates items in the series, including the final item preceded by `coordinator` which should be a
    coordinating conjunction, typically :const:`'and'`, :const:`'or'`, or :const:`'nor'`.

    :param series: An object that iterates over items in a series.
    :type series: :type:`collections.abc.Iterable`

    :param coordinator: a coordinating conjunction, typically :const:`'and'`, `'or', or :const:``nor``. The default
    value is :const:`'and'`.
    :type coordinator: :type:`string`

    :return: A string representing the items in a series.
    :rtype: :type:`string`

    """

    def items():
        iterator = iter(series)

        try:
            item = next(iterator)
        except StopIteration:
            return

        yield string(item)

        try:
            item = next(iterator)
        except StopIteration:
            return

        previous_item = item
        count = 2

        for count, item in enumerate(iterator, 3):
            yield ", "
            yield string(previous_item)
            previous_item = item

        yield " " if count == 2 else ", "
        yield coordinator
        yield " "
        yield string(item)

    return "".join(items())


def escape_non_alphanumeric_chars(pattern):
    """
    Escape all non-alphanumeric characters in pattern
    :param pattern input string
    :return escaped input string
    """
    input = list(pattern)
    for i, char in enumerate(pattern):
        if not char.isalnum():
            if char == "\000":
                input[i] = "\\000"
            else:
                input[i] = "\\" + char
    return pattern[:0].join(input)
