from flask import Blueprint, current_app

from .utils import api_response, login_required

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.get("/overview")
@login_required()
def overview():
    return api_response(current_app.extensions["dashboard_service"].overview())

