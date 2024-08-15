from flask import request
from urllib.parse import urlparse, urljoin


def is_relative_path(path: str):
    """ Returns whether the URL path is relative. """
    parsed_url = urlparse(path)
    return not parsed_url.netloc and not parsed_url.scheme


def is_internal_path(path: str):
    """ Returns whether the URL path is internal. """
    if is_relative_path(path):
        return True
    ref_url = urlparse(request.host_url)
    parsed_url = urlparse(path)
    return parsed_url.scheme in ('http', 'https') and ref_url.netloc == parsed_url.netloc
