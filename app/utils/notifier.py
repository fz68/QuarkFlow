"""Telegram notification service."""

import logging
from telethon import TelegramClient
from telethon.errors import MessageEmptyError

from app.config import TG_API_ID, TG_API_HASH, TG_SESSION_NAME

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self.client = TelegramClient(f"data/{TG_SESSION_NAME}", TG_API_ID, TG_API_HASH)

    async def start(self):
        await self.client.start()
        logger.info("Notifier: Telegram client started")

    async def send_cookie_expired_alert(self, error_message: str = ""):
        try:
            me = await self.client.get_me()
            user_id = me.id

            message = f"""⚠️ QuarkFlow Cookie 已过期！

错误信息：{error_message}

请立即更新：
1. 访问 http://your-vps:8080/login
2. 重新获取 Cookie
3. 重启容器：docker compose restart

Cookie 过期会导致转存失败。"""

            await self.client.send_message(user_id, message)
            logger.info("Notifier: Cookie expired alert sent")

        except MessageEmptyError:
            logger.error("Notifier: Failed to send message - empty message")
        except Exception as e:
            logger.error(f"Notifier: Failed to send alert: {e}")

    async def stop(self):
        await self.client.disconnect()
        logger.info("Notifier: Telegram client disconnected")
