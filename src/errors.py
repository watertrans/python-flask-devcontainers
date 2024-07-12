from flask import Blueprint, render_template, abort

bp = Blueprint("errors", __name__)


@bp.route('/errors/bad-request')
def bad_request():
    """ Raise a "Bad Request" error. """
    abort(400)


@bp.route('/errors/unauthorized')
def unauthorized():
    """ Raise an "Unauthorized" error. """
    abort(401)


@bp.route('/errors/forbidden')
def forbidden():
    """ Raise a "Forbidden" error. """
    abort(403)


@bp.route('/errors/not-found')
def not_found():
    """ Raise a "Not Found" error. """
    abort(404)


@bp.route('/errors/method-not-allowed')
def method_not_allowed():
    """ Raise a "Method Not Allowed" error. """
    abort(405)


@bp.route('/errors/conflict')
def conflict():
    """ Raise a "Conflict" error. """
    abort(409)


@bp.route('/errors/gone')
def gone():
    """ Raise a "Gone" error. """
    abort(410)


@bp.route('/errors/server-error')
def server_error():
    """ Raise an "Internal Server Error". """
    abort(500)


@bp.route('/errors/not-implemented')
def not_implemented():
    """ Raise a "Not Implemented" error. """
    abort(501)


@bp.route('/errors/service-unavailable')
def service_unavailable():
    """ Raise a "Service Unavailable" error. """
    abort(503)


@bp.app_errorhandler(400)
def handle_bad_request(error: Exception):
    """ Handles the error code of 400. """
    return render_template('errors/bad_request.html'), 400


@bp.app_errorhandler(401)
def handle_unauthorized(error: Exception):
    """ Handles the error code of 401. """
    return render_template('errors/unauthorized.html'), 401


@bp.app_errorhandler(403)
def handle_forbidden(error: Exception):
    """ Handles the error code of 403. """
    return render_template('errors/forbidden.html'), 403


@bp.app_errorhandler(404)
def handle_not_found(error: Exception):
    """ Handles the error code of 404. """
    return render_template('errors/not_found.html'), 404


@bp.app_errorhandler(405)
def handle_method_not_allowed(error: Exception):
    """ Handles the error code of 405. """
    return render_template('errors/method_not_allowed.html'), 405


@bp.app_errorhandler(409)
def handle_conflict(error: Exception):
    """ Handles the error code of 409. """
    return render_template('errors/conflict.html'), 409


@bp.app_errorhandler(410)
def handle_gone(error: Exception):
    """ Handles the error code of 410. """
    return render_template('errors/gone.html'), 410


@bp.app_errorhandler(500)
def handle_server_error(error: Exception):
    """ Handles the error code of 500. """
    return render_template('errors/server_error.html'), 500


@bp.app_errorhandler(501)
def handle_not_implemented(error: Exception):
    """ Handles the error code of 501. """
    return render_template('errors/not_implemented.html'), 501


@bp.app_errorhandler(503)
def handle_service_unavailable(error: Exception):
    """ Handles the error code of 503. """
    return render_template('errors/service_unavailable.html'), 503
