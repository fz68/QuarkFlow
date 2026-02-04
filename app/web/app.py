"""Web UI for QuarkFlow configuration."""

from flask import Flask, render_template, request, jsonify
import logging
import os
import asyncio
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import string
import random

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "quarkflow-secret-key")

BASE_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

telegram_login_sessions = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/telegram/login")
def telegram_login():
    return render_template("telegram_login.html")


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
    from app.config import QUARK_COOKIE, TG_SESSION_NAME, DATA_DIR

    TG_SESSION_FILE = DATA_DIR / f"{TG_SESSION_NAME}.session"
    telegram_configured = TG_SESSION_FILE.exists()

    return jsonify(
        {
            "quark_configured": bool(QUARK_COOKIE),
            "telegram_configured": telegram_configured,
        }
    )


@app.route("/api/telegram/send-code", methods=["POST"])
def send_telegram_code():
    from app.config import TG_API_ID, TG_API_HASH, TG_SESSION_NAME, DATA_DIR

    data = request.json
    phone = data.get("phone", "").strip()

    if not phone:
        return jsonify({"success": False, "error": "Phone number is required"}), 400

    if not TG_API_ID or not TG_API_HASH:
        return jsonify(
            {"success": False, "error": "Telegram API credentials not configured"}
        ), 500

    phone_hash = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    TG_SESSION_FILE = DATA_DIR / f"{TG_SESSION_NAME}.session"

    async def send_code():
        client = TelegramClient(str(TG_SESSION_FILE), TG_API_ID, TG_API_HASH)
        try:
            await client.connect()
            result = await client.send_code_request(phone)
            await client.disconnect()
            telegram_login_sessions[phone_hash] = {
                "phone": phone,
                "phone_code_hash": result.phone_code_hash,
            }
            return {"success": True, "phone_hash": phone_hash}
        except Exception as e:
            logger.error(f"Failed to send code: {e}")
            await client.disconnect()
            return {"success": False, "error": str(e)}

    result = asyncio.run(send_code())
    return jsonify(result)


@app.route("/api/telegram/sign-in", methods=["POST"])
def sign_in_telegram():
    from app.config import TG_API_ID, TG_API_HASH, TG_SESSION_NAME, DATA_DIR

    data = request.json
    phone_hash = data.get("phone_hash", "")
    code = data.get("code", "").strip()
    password = data.get("password", "")

    if phone_hash not in telegram_login_sessions:
        return jsonify({"success": False, "error": "Invalid or expired session"}), 400

    session = telegram_login_sessions[phone_hash]
    TG_SESSION_FILE = DATA_DIR / f"{TG_SESSION_NAME}.session"

    async def do_sign_in():
        client = TelegramClient(str(TG_SESSION_FILE), TG_API_ID, TG_API_HASH)
        try:
            await client.connect()
            if password:
                await client.sign_in(password=password)
            else:
                await client.sign_in(
                    session["phone"], code, phone_code_hash=session["phone_code_hash"]
                )

            await client.disconnect()

            del telegram_login_sessions[phone_hash]

            return {"success": True}
        except SessionPasswordNeededError:
            await client.disconnect()
            return {
                "success": False,
                "error": "Two-factor authentication enabled",
                "requires_password": True,
            }
        except Exception as e:
            logger.error(f"Failed to sign in: {e}")
            await client.disconnect()
            return {"success": False, "error": str(e)}

    result = asyncio.run(do_sign_in())
    return jsonify(result)


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
