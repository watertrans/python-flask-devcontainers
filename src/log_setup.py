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
    logger.setLevel(_log_setup.log_level)
    logger.addHandler(_log_setup.stdout_handler)
    logger.addHandler(_log_setup.stderr_handler)

    return logger


class LogfmtFormatter(log.Formatter):
    def format(self, record: log.LogRecord):
        log_record = (
            f"time={self.formatTime(record, self.datefmt)} "
            f"level={record.levelname} "
            f"message=\"{record.getMessage().replace(
                '"', '\\"').replace("\n", "\\n")}\" "
            f"name={record.name} "
            f"file={record.filename} "
            f"func={record.funcName} "
            f"lineno={record.lineno}"
        )
        return log_record


class LogSetup:
    def __init__(self):
        # Set log output format
        self.format = "%(asctime)s %(levelname)s %(name)s %(message)s [%(filename)s:%(lineno)d:%(funcName)s()]"
        self.formatter = LogfmtFormatter()
        self.formatter.formatTime = format_log_time

        # WARNING and lower level logs are output to stdout
        self.stdout_handler = log.StreamHandler(sys.stdout)
        self.stdout_handler.setLevel(log.NOTSET)
        self.stdout_handler.addFilter(
            lambda record: record.levelno <= log.WARNING)
        self.stdout_handler.setFormatter(self.formatter)

        # ERROR and CRITICAL level logs are output to stderr
        self.stderr_handler = log.StreamHandler(sys.stderr)
        self.stderr_handler.setLevel(log.ERROR)
        self.stderr_handler.setFormatter(self.formatter)

        # The log output level can be controlled by environment variables. The default and invalid value is INFO.
        log_level_str = getattr(log, os.getenv(
            "LOG_LEVEL", "INFO").upper(), None)
        if not isinstance(log_level_str, int):
            self.log_level = log.INFO
        else:
            self.log_level = log_level_str


_log_setup = LogSetup()
