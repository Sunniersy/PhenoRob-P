import os

import click
from flask import current_app

from backend.app.validators import validate_bootstrap_admin_payload
from shared.demo_support import DEFAULT_DEMO_ADMIN_PASSWORD, DEFAULT_DEMO_ADMIN_USERNAME


def _alembic_config():
    from alembic.config import Config as AlembicConfig

    config = AlembicConfig("alembic.ini")
    config.set_main_option("sqlalchemy.url", current_app.config["DATABASE_URL"])
    return config


def register_cli(app):
    @app.cli.command("seed")
    def seed():
        current_app.extensions["auth_service"].ensure_roles()
        click.echo("System roles ensured.")

    @app.cli.command("db-upgrade")
    def db_upgrade():
        from alembic import command

        command.upgrade(_alembic_config(), "head")
        click.echo("Database upgraded.")

    @app.cli.command("demo-reset-admin")
    @click.option("--username", default=None, help="Override the demo admin username for this run.")
    @click.option("--password", default=None, help="Override the demo admin password for this run.")
    def demo_reset_admin(username, password):
        resolved_username = username or os.getenv("BOOTSTRAP_ADMIN_USERNAME") or os.getenv(
            "DEFAULT_ADMIN_USERNAME", DEFAULT_DEMO_ADMIN_USERNAME
        )
        resolved_password = password or os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or os.getenv(
            "DEFAULT_ADMIN_PASSWORD", DEFAULT_DEMO_ADMIN_PASSWORD
        )
        payload = validate_bootstrap_admin_payload(
            {"username": resolved_username, "password": resolved_password},
            min_length=current_app.config["PASSWORD_MIN_LENGTH"],
        )
        result = current_app.extensions["auth_service"].sync_demo_admin(payload["username"], payload["password"])
        click.echo(f"Demo admin synced: {result['user']['username']}")
