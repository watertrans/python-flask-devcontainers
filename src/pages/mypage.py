from clients import AssuranceLevel
from decorators import signin_required
from flask import Blueprint, render_template, request, session
from forms import *
import messages

bp = Blueprint("mypage", __name__)


@bp.route(rule="/mypage/", methods=["GET"])
@signin_required(AssuranceLevel.TWO)
def index():
    """ Displays the my page screen. """
    return render_template("mypage/index.html", localized=messages)
