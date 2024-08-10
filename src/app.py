from clients import AuthClient
from context_processor import utility_processor
from dotenv import load_dotenv
from errors import bp as errors_bp
from flask import Config, Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask.logging import default_handler
from pages import bp as pages_bp
from services import AuthService
from typing import Any
import datetime
import inject
import json
import logging as log
import os
import sys
import yaml


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


def setup_config(app: Flask):
    """
    Sets up the config.
    """
    with open("config.yaml", "r") as file:
        config: dict[str, Any] = yaml.safe_load(file)
        app.config.update(config)

    app.config.from_prefixed_env()


def setup_logger(app: Flask):
    """
    Sets up the logger.
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


def setup_session(app: Flask):
    """
    Sets up the session.
    """

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sessions.db"
    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_KEY_PREFIX"] = "session:"

    db = SQLAlchemy(app)
    app.config["SESSION_SQLALCHEMY"] = db
    Session(app)

    with app.app_context():
        db.create_all()


def setup_container(binder: inject.Binder):
    """
    Sets up the dependency injection container.
    """

    auth_client = AuthClient(app.config)
    auth_service = AuthService(app.config, auth_client)

    binder.bind(Config, app.config)
    binder.bind(AuthClient, auth_client)
    binder.bind(AuthService, auth_service)


load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.logger.removeHandler(default_handler)
app.register_blueprint(pages_bp)
app.register_blueprint(errors_bp)
app.context_processor(utility_processor)

setup_config(app)
setup_logger(app)
setup_session(app)
inject.configure(setup_container)

app.logger.info("App started.")
