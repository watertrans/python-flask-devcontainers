from flask import Blueprint, render_template, abort

bp = Blueprint("errors", __name__)

@bp.route('/errors/bad_request')
def bad_request():
    abort(400)

@bp.app_errorhandler(400)
def handle_bad_request(error: Exception):
    return render_template('errors/bad_request.html'), 400

@bp.route('/errors/not_found')
def not_found():
    abort(404)

@bp.app_errorhandler(404)
def handle_not_found(error: Exception):
    return render_template('errors/not_found.html'), 404

@bp.route('/errors/method_not_allowed')
def method_not_allowed():
    abort(405)

@bp.app_errorhandler(405)
def handle_method_not_allowed(error: Exception):
    return render_template('errors/method_not_allowed.html'), 405

@bp.route('/errors/server_error')
def server_error():
    abort(500)

@bp.app_errorhandler(500)
def handle_server_error(error: Exception):
    return render_template('errors/server_error.html'), 500
