from flask import Flask 
from core.config import Config
from extensions.database import db, migrate, login_manager 
from models import modelos 
from routes.__init__ import routes_app 

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app,db)

    # Configuração do Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Aponta para o blueprint 'auth'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    routes_app(app)

    return app

app = create_app()

if __name__== '__main__':
    app.run(port=5000, debug=True)