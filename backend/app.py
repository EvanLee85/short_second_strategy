# -*- coding: utf-8 -*-
from flask import Flask
from flask_cors import CORS
from loguru import logger
from backend.api.routes import api_bp

def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    @app.get("/")
    def root():
        return {"ok": True, "service": "trading-system-backend"}

    return app

app = create_app()

if __name__ == "__main__":
    # 确保从项目根目录运行： export PYTHONPATH=$(pwd)
    logger.info("Starting backend on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
