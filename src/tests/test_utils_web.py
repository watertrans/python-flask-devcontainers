from unittest.mock import patch
from flask import Flask
import pytest
import utils.web


@pytest.fixture
def app():
    app = Flask(__name__)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_is_relative_path():
    assert utils.web.is_relative_path("home") is True
    assert utils.web.is_relative_path("/home") is True
    assert utils.web.is_relative_path("../home") is True
    assert utils.web.is_relative_path("home/path") is True
    assert utils.web.is_relative_path("http://localhost") is False
    assert utils.web.is_relative_path("http://localhost:5000") is False
    assert utils.web.is_relative_path("https://localhost") is False
    assert utils.web.is_relative_path("ftp://localhost") is False
    assert utils.web.is_relative_path("app:localhost") is False


def test_is_internal_path(app):
    with app.test_request_context(base_url="http://localhost:5000"):
        assert utils.web.is_internal_path('/relative/path') is True
        assert utils.web.is_internal_path('../relative/path') is True
        assert utils.web.is_internal_path('relative/path') is True
        assert utils.web.is_internal_path('http://localhost:5000/some/path') == True
        assert utils.web.is_internal_path('http://external.com/some/path') == False
        assert utils.web.is_internal_path('ftp://localhost:5000/some/path') == False
