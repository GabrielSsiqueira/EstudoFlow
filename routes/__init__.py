from .auth import auth_bp
from .admin import admin_bp
from .user import user_bp
from .main import main_bp


def routes_app(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)