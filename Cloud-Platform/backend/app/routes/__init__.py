from backend.app.routes.admin import bp as admin_bp
from backend.app.routes.assets import bp as assets_bp
from backend.app.routes.auth import bp as auth_bp
from backend.app.routes.dashboard import bp as dashboard_bp
from backend.app.routes.downloads import bp as downloads_bp
from backend.app.routes.results import bp as results_bp
from backend.app.routes.robots import bp as robots_bp
from backend.app.routes.system import bp as system_bp
from backend.app.routes.tasks import bp as tasks_bp


def register_blueprints(app):
    for bp in [auth_bp, tasks_bp, robots_bp, assets_bp, results_bp, dashboard_bp, system_bp, admin_bp, downloads_bp]:
        app.register_blueprint(bp)
