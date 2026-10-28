import os
from flask import Flask
from app.models import init_db

def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )
    app.config.from_mapping(
        SECRET_KEY="cleanmail-secret-key-348271",
        DATABASE=os.path.join(app.instance_path, "cleanmail.sqlite"),
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    init_db(app.config["DATABASE"])

    from app.routes import bp
    app.register_blueprint(bp)

    return app
