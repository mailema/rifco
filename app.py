"""
RIFCO - Ringim Football Coaches Organization
Application entry point.

Run locally with:
    python app.py

Or with the Flask CLI:
    flask --app app run
"""

import os

from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()  # loads .env into the environment before Config reads it

from config import Config
from extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ---- extensions --------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)

    try:
        from flask_wtf import CSRFProtect
        CSRFProtect(app)
    except ImportError:
        app.logger.warning("Flask-WTF not installed - CSRF protection is disabled.")

    # ---- models must be imported after db.init_app so Flask-Login's
    # user_loader and db.create_all() can see every table -------------
    from models import Member

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Member, int(user_id))

    # ---- blueprints ----------------------------------------------
    from routes.public import public_bp
    from routes.auth import auth_bp
    from routes.chairman import chairman_bp
    from routes.coach import coach_bp
    from routes.transfer import transfer_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chairman_bp)
    app.register_blueprint(coach_bp)
    app.register_blueprint(transfer_bp)

    # ---- error handlers --------------------------------------------
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # ---- template context --------------------------------------------
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {"current_year": datetime.utcnow().year}

    @app.template_global()
    def picture_url(picture):
        """Resolve a Player.picture value to a renderable <img> src.

        Older records (saved before Vercel Blob was wired up, or
        anything saved during local development) hold a path
        relative to the static folder. Newer records hold a full
        https:// URL from Vercel Blob. Templates just call
        picture_url(player.picture) and don't need to know which
        kind they have.
        """
        if not picture:
            return ""
        if picture.startswith("http://") or picture.startswith("https://"):
            return picture
        from flask import url_for
        return url_for("static", filename=picture)

    # ---- dev-only table creation -------------------------------------
    # Never drops or recreates existing data. If the database already
    # has these tables, this is a no-op.
    with app.app_context():
        db.create_all()
        if app.config.get("USING_FALLBACK_DATABASE"):
            app.logger.warning(
                "DATABASE_URL is not set - using a local SQLite fallback "
                "(rifco_dev.db) for development only. Configure DATABASE_URL "
                "with a real Postgres/Neon connection string before deploying."
            )

    return app


app = create_app()


if __name__ == "__main__":
    debug_mode = app.config["DEBUG"]
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)
