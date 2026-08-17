import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret")
    database_url = os.environ.get("DATABASE_URL", "sqlite:///digitalhub.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

    upload_root = os.environ.get("UPLOAD_FOLDER", os.path.join(app.root_path, "static", "uploads"))
    os.makedirs(upload_root, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_root

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.admin_login"

    from .models import Admin
    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            admin = Admin(username=os.environ.get("ADMIN_USERNAME", "admin"))
            admin.set_password(os.environ.get("ADMIN_PASSWORD", "change-me-now"))
            db.session.add(admin)
            db.session.commit()

    return app
