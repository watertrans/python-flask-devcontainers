from errors import bp as errors_bp
from pages import bp as pages_bp
from flask import Flask
from flask.logging import default_handler
import logging as log
import datetime
import sys
import os
import json


class LogfmtFormatter(log.Formatter):
    def format(self, record: log.LogRecord):
        """
        Configure log output in logfmt format.
        """
        log_record = (
            f"time={self.formatTime(record, self.datefmt)} "
            f"level={record.levelname} "
            f"message={self.escape_message(record.getMessage())} "
            f"name={record.name} "
            f"file={record.filename} "
            f"func={record.funcName} "
            f"lineno={record.lineno}"
        )

        if record.exc_info:
            log_record += f" exception={self.escape_message(
                self.formatException(record.exc_info))}"

        return log_record

    def escape_message(self, message: str):
        """
        Escapes newline characters and double quotes.
        """
        if not message:
            return message
        else:
            return '"' + message.replace('"', '\\"').replace("\n", "\\n") + '"'


class JsonFormatter(log.Formatter):
    def format(self, record: log.LogRecord):
        """
        Configure log output in json format.
        """
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
            "file": record.filename,
            "func": record.funcName,
            "lineno": record.lineno,
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


def format_log_time(record: log.LogRecord, datefmt: str | None = None):
    """
    Convert log time to ISO8601 format.
    """
    return datetime.datetime.fromtimestamp(record.created).astimezone().isoformat("T", "milliseconds")


def setup_logger(app: Flask):
    """
    This function sets and returns the logger.
    """

    # Set log output format
    formatter = JsonFormatter()
    formatter.formatTime = format_log_time

    # WARNING and lower level logs are output to stdout
    stdout_handler = log.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log.NOTSET)
    stdout_handler.addFilter(
        lambda record: record.levelno <= log.WARNING)
    stdout_handler.setFormatter(formatter)

    # ERROR and CRITICAL level logs are output to stderr
    stderr_handler = log.StreamHandler(sys.stderr)
    stderr_handler.setLevel(log.ERROR)
    stderr_handler.setFormatter(formatter)

    # The log output level can be controlled by environment variables. The default and invalid value is INFO.
    log_level_str = getattr(log, os.getenv(
        "LOG_LEVEL", "INFO").upper(), None)
    if not isinstance(log_level_str, int):
        log_level = log.INFO
    else:
        log_level = log_level_str

    app.logger.setLevel(log_level)
    app.logger.addHandler(stdout_handler)
    app.logger.addHandler(stderr_handler)


app = Flask(__name__)
app.logger.removeHandler(default_handler)
app.register_blueprint(pages_bp)
app.register_blueprint(errors_bp)
setup_logger(app)
app.logger.info("App started.")
