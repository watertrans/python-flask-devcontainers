from errors import bp as errors_bp
from pages import bp as pages_bp
from flask import Flask
from log_setup import setup_logger

logger = setup_logger(__name__)

app = Flask(__name__)
app.register_blueprint(pages_bp)
app.register_blueprint(errors_bp)
