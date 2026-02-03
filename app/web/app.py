"""Web UI for QuarkFlow configuration."""

from flask import Flask, render_template, request, jsonify
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "quarkflow-secret-key")

BASE_DIR = Path(__file__).parent.parent
ENV_FILE = BASE_DIR / ".env"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/api/cookie", methods=["POST"])
def update_cookie():
    data = request.json

    cookie = data.get("cookie", "").strip()

    if not cookie:
        return jsonify({"success": False, "error": "Cookie is required"}), 400

    try:
        update_env_file(
            {
                "QUARK_COOKIE": f'"{cookie}"',
            }
        )

        logger.info("Cookie updated via WebUI")

        return jsonify(
            {
                "success": True,
                "message": "Cookie updated successfully. Please restart the container.",
            }
        )

    except Exception as e:
        logger.error(f"Failed to update cookie: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/status")
def status():
    from app.config import QUARK_COOKIE

    return jsonify(
        {
            "quark_configured": bool(QUARK_COOKIE),
        }
    )


def update_env_file(updates):
    env_content = ENV_FILE.read_text()

    for key, value in updates.items():
        import re

        pattern = f"^{key}=.*$"
        replacement = f"{key}={value}"

        if re.search(pattern, env_content, re.MULTILINE):
            env_content = re.sub(pattern, replacement, env_content, flags=re.MULTILINE)
        else:
            env_content += f"\n{key}={value}"

    ENV_FILE.write_text(env_content)


def run_web_server(host="0.0.0.0", port=8080):
    logger.info(f"Starting WebUI on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_web_server()
