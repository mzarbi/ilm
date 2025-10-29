from flask import Flask
from flask_cors import CORS

from .client import ilm_bp
from .database import init_session_factory
from .errors import errors_bp
from .api.routes import api_bp
import os

# server/__init__.py
from flask import Flask
import server.extensions as ext
from server.database import init_session_factory
from server.api.routes import api_bp
from server.errors import errors_bp

def create_app(engine=None) -> Flask:
    app = Flask(__name__)
    if engine is not None:
        ext.ENGINE = engine
        init_session_factory()

    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:3000"]}},
        expose_headers=["X-App-Env"],
        supports_credentials=False,
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.after_request
    def add_env_header(resp):
        resp.headers['X-App-Env'] = os.getenv('APP_ENV', 'dev')
        return resp

    app.register_blueprint(errors_bp)
    app.register_blueprint(api_bp)

    app.register_blueprint(ilm_bp, url_prefix="/ilm")
    return app
