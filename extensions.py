"""
Extension instances are created here (not bound to an app yet) so
models.py and the route blueprints can import them without causing
circular imports. app.py binds them to the real app with init_app().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access that page."
login_manager.login_message_category = "warning"
