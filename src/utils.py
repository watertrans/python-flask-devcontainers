import datetime
import logging as log
import sys
import os


def format_log_time(record: log.LogRecord, datefmt: str | None = None):
    """
    Convert log time to ISO8601 format.
    """
    return datetime.datetime.fromtimestamp(record.created).astimezone().isoformat("T", "milliseconds")


def setup_logger(name: str):
    """
    This function sets and returns the logger.
    """

    logger = log.getLogger(name)
    logger.setLevel(_log_level)
    logger.addHandler(_stdout_handler)
    logger.addHandler(_stderr_handler)

    return logger


_formatter = log.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s [%(filename)s:%(lineno)d:%(funcName)s()]")
_formatter.formatTime = format_log_time

# WARNING and lower level logs are output to stdout
_stdout_handler = log.StreamHandler(sys.stdout)
_stdout_handler.setLevel(log.NOTSET)
_stdout_handler.addFilter(lambda record: record.levelno <= log.WARNING)
_stdout_handler.setFormatter(_formatter)

# ERROR and CRITICAL level logs are output to stderr
_stderr_handler = log.StreamHandler(sys.stderr)
_stderr_handler.setLevel(log.ERROR)
_stderr_handler.setFormatter(_formatter)

# The log output level can be controlled by environment variables. The default and invalid value is INFO.
_log_level_str = os.getenv("LOG_LEVEL", "INFO")
_log_level_parsed = getattr(log, _log_level_str.upper(), None)
if not isinstance(_log_level_parsed, int):
    _log_level = log.INFO
else:
    _log_level = _log_level_parsed
