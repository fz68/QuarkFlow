"""Telegram listener for QuarkFlow."""

import logging
import re
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

from app.config import TG_API_ID, TG_API_HASH, TG_CHANNEL, TG_SESSION_NAME
from app.db import insert_tg_message, insert_share_pending

logger = logging.getLogger(__name__)


def extract_quark_links(text: str) -> list[str]:
    if not text:
        return []

    pattern = r"pan\.quark\.cn/s/([a-zA-Z0-9]+)"
    matches = re.findall(pattern, text)
    return matches


class TelegramListener:
    def __init__(self):
        self.client = TelegramClient(f"data/{TG_SESSION_NAME}", TG_API_ID, TG_API_HASH)

    async def start(self):
        await self.client.start()
        logger.info(f"Logged in as {await self.client.get_me()}")

    async def on_new_message(self, event):
        message = event.message

        channel_id = event.chat.username if event.chat else "unknown"
        message_id = message.id
        message_text = message.text or ""

        logger.info(f"[TELEGRAM] new message id={message_id} from @{channel_id}")

        if not extract_quark_links(message_text):
            logger.debug(f"[TELEGRAM] no quark link in message {message_id}")
            return

        if not insert_tg_message(f"@{channel_id}", message_id):
            logger.info(f"[DEDUP] message {message_id} already processed")
            return

        share_ids = extract_quark_links(message_text)
        for share_id in share_ids:
            logger.info(f"[LINK] found pan.quark.cn/s/{share_id}")

            if not insert_share_pending(share_id):
                logger.info(f"[DEDUP] share_id={share_id} already exists")
                continue

            logger.info(f"[NEW] share_id={share_id} queued for processing")

    async def listen(self):
        self.client.add_event_handler(
            self.on_new_message, events.NewMessage(chats=TG_CHANNEL)
        )

        logger.info(f"Listening for messages in {TG_CHANNEL}...")
        await self.client.run_until_disconnected()

    async def stop(self):
        await self.client.disconnect()
        logger.info("Telegram client disconnected")
