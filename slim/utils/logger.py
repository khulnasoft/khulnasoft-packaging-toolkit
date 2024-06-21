#!/usr/bin/env python
# coding=utf-8
#
# Copyright © KhulnaSoft, Ltd. All Rights Reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import object
from traceback import format_tb
import logging
import sys
from os.path import basename, splitext

from .internal import string

__all__ = ["SlimLogger", "SlimExternalFormatter"]


logging.STEP = logging.INFO - 1
logging.addLevelName(logging.STEP, "STEP")


class SlimFormatter(logging.Formatter):
    """
    Format CLI messages to include the level name prefix strings we want
    For example, <command>: <level_name> <message + args>
    """

    # noinspection PyShadowingBuiltins
    def __init__(self, formatstr):
        logging.Formatter.__init__(self, formatstr)

    def format(self, record):
        record.levelname = self._level_names.get(record.levelno, " ")
        record.msg = "%s" * len(record.args)
        return logging.Formatter.format(self, record)

    _level_names = {
        logging.DEBUG: " [DEBUG] ",
        logging.INFO: " [INFO] ",
        logging.WARN: " [WARNING] ",
        logging.ERROR: " [ERROR] ",
        logging.FATAL: " [FATAL] ",
    }


class SlimExternalFormatter(logging.Formatter):
    """
    Provide a formatter for clients of the API to use, which does not use the
    same formatting at the CLI output (for raw message + args output)
    """

    # noinspection PyShadowingBuiltins
    def __init__(self, formatstr):
        logging.Formatter.__init__(self, formatstr)

    def format(self, record):
        record.msg = "%s" * len(record.args)
        return logging.Formatter.format(self, record)


class SlimLogger(object):
    """
    All SLIM logging, configuration, and tracking is routed through the SlimLogger
    """

    # region Logging and logging count methods

    @classmethod
    def debug(cls, *args):
        cls._emit(logging.DEBUG, *args)

    @classmethod
    def error(cls, *args):
        cls._emit(logging.ERROR, *args)

    @classmethod
    def error_count(cls):
        return cls._message_count[logging.ERROR]

    @classmethod
    def fatal(cls, *args, **kwargs):

        exception_info = kwargs.get("exception_info")

        if exception_info is None:
            cls._emit(logging.FATAL, *args)
        else:
            error_type, error_value, traceback = exception_info

            message = string(
                error_type.__name__ if error_value is None else error_value
            )

            if cls._debug:
                message += (
                    "\nTraceback: "
                    + error_type.__name__
                    + "\n"
                    + "".join(format_tb(traceback))
                )

            cls._emit(
                logging.FATAL, *(args + (": ", message)) if len(args) > 0 else message
            )

        sys.exit(1)

    @classmethod
    def information(cls, *args):
        cls._emit(logging.INFO, *args)

    @classmethod
    def step(cls, *args):
        cls._emit(logging.STEP, *args)

    @classmethod
    def warning(cls, *args):
        cls._emit(logging.WARN, *args)

    @classmethod
    def message(cls, level, *args, **kwargs):
        if str(level) == level:
            level = (
                logging.INFO
                if level not in cls._level_names
                else cls._level_names[level.upper()]
            )
        if level != logging.FATAL:
            cls._emit(level, *args)
            return
        cls.fatal(*args, **kwargs)

    @classmethod
    def reset_counts(cls):
        for level in cls._message_count:
            cls._message_count[level] = 0

    @classmethod
    def exit_on_error(cls):
        if cls._message_count[logging.ERROR]:
            sys.exit(1)

    # endregion

    # region Logging configuration methods

    @classmethod
    def set_debug(cls, value):
        cls._debug = bool(value)

    @classmethod
    def is_debug_enabled(cls):
        return cls._debug is True

    @classmethod
    def set_level(cls, value):
        cls._logger.setLevel(value)  # setLevel() handles both numeric and string levels
        cls._default_level = cls._logger.level  # this level value is always numeric

    @classmethod
    def set_command_name(cls, command_name):
        cls._adapter = logging.LoggerAdapter(
            cls._logger, {"command_name": command_name}
        )

    # endregion

    # region Logging handlers

    @classmethod
    def add_handler(cls, handler):
        cls._logger.addHandler(handler)

    @classmethod
    def remove_handler(cls, handler):
        cls._logger.removeHandler(handler)

    @classmethod
    def handlers(cls):
        return cls._logger.handlers

    @classmethod
    def use_external_handler(cls, handler):
        cls.remove_handler(cls._handler)
        cls.add_handler(handler)

    # endregion

    # region Privates

    _debug = False  # turns on debug output which is different than turning on debug messages using, e.g., set_level
    _default_level = (
        logging.STEP
    )  # call SlimLogger.set_level to change (works in tandem with SlimLogger.set_quiet)

    _message_count = {
        logging.STEP: 0,
        logging.DEBUG: 0,
        logging.INFO: 0,
        logging.WARN: 0,
        logging.ERROR: 0,
        logging.FATAL: 0,
    }

    # This is a copy of logging/__init__.py:_levelNames because the logging library does not expose this mapping
    # It only exposes the number => string mapping via getLevelName()
    _level_names = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARN": logging.WARNING,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "STEP": logging.STEP,  # custom logging level
        "NOTE": logging.INFO,  # backwards compatibility
    }

    # noinspection PyShadowingNames
    @classmethod
    def _emit(cls, level, *args):
        cls._adapter.log(level, None, *args)
        cls._message_count[level] += 1

    @staticmethod
    def _initialize_logging():

        command_name = splitext(basename(sys.argv[0]))[0]
        if not command_name:
            # Make sure we have a non-empty command name, even when loaded as a library
            # The command name is used to grab and configure a unique non-root logger
            command_name = "slim"

        logger = logging.getLogger(command_name)
        logger.setLevel(logging.STEP)
        logger.propagate = False  # do not try to use parent logging handlers

        handler = logging.StreamHandler()
        handler.setFormatter(SlimFormatter("%(command_name)s:%(levelname)s%(message)s"))
        logger.addHandler(handler)

        adapter = logging.LoggerAdapter(logger, {"command_name": command_name})

        return logger, handler, adapter

    _logger, _handler, _adapter = _initialize_logging.__func__()

    # endregion
    pass  # pylint: disable=unnecessary-pass
