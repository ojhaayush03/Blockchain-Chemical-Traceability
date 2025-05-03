from flask import Flask
from app.extensions import db
from app.routes import dashboard_bp, main  # <-- Import both blueprints from the `routes` package

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chemicals.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(main)

    return app
