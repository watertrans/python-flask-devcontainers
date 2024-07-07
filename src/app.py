import logging as log
import sys
import os

def setup_logger():
    """
    This function sets and returns the logger.
    """

    # WARNING and lower level logs are output to stdout
    stdout_handler = log.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log.NOTSET)
    stdout_handler.addFilter(lambda record: record.levelno <= log.WARNING)

    # ERROR and CRITICAL level logs are output to stderr
    stderr_handler = log.StreamHandler(sys.stderr)
    stderr_handler.setLevel(log.ERROR)

    logger = log.getLogger('Python DevContainers')

    # The log output level can be controlled by environment variables. The default and invalid value is INFO.
    log_level_str = os.getenv("LOG_LEVEL", "INFO")
    log_level = getattr(log, log_level_str.upper(), None)
    if not isinstance(log_level, int):
        log_level = log.INFO
    logger.setLevel(log_level)
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    return logger

logger = setup_logger()

from flask import Flask
from pages import bp as pages_bp
from errors import bp as errors_bp

app = Flask(__name__)
app.register_blueprint(pages_bp)
app.register_blueprint(errors_bp)
