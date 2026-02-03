import asyncio
import logging
from app.db import get_pending_tasks, mark_share_saved, mark_share_failed
from app.config import WORKER_POLL_INTERVAL, WORKER_CONCURRENT_TASKS
from app.quark.client import QuarkClient
from app.utils.notifier import TelegramNotifier

logger = logging.getLogger(__name__)


class QuarkWorker:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(WORKER_CONCURRENT_TASKS)
        self.running = False
        self.quark_client = QuarkClient()
        self.notifier = TelegramNotifier()
        self.cookie_expired_notified = False

    async def process_task(self, share_id: str):
        async with self.semaphore:
            logger.info(f"[WORKER] processing share_id={share_id}")

            try:
                result = await self.quark_client.save_share(share_id=share_id)

                if result["success"]:
                    task_id = result.get("task_id", "")
                    logger.info(f"[WORKER] done, status=saved, task_id={task_id}")
                    mark_share_saved(share_id, task_id)

                    if self.cookie_expired_notified:
                        self.cookie_expired_notified = False
                        logger.info("Cookie is working again, cleared expired flag")

                else:
                    error = result.get("error", "Unknown error")

                    if result.get("cookie_expired"):
                        logger.error(f"[WORKER] Cookie expired: {error}")

                        if not self.cookie_expired_notified:
                            await self.notifier.start()
                            await self.notifier.send_cookie_expired_alert(error)
                            await self.notifier.stop()
                            self.cookie_expired_notified = True

                        mark_share_failed(share_id, f"Cookie expired: {error}")
                    else:
                        logger.error(
                            f"[WORKER] failed for share_id={share_id}: {error}"
                        )
                        mark_share_failed(share_id, error)

            except Exception as e:
                logger.error(f"[WORKER] exception for share_id={share_id}: {e}")
                mark_share_failed(share_id, str(e))

    async def run(self):
        self.running = True
        logger.info(f"Worker started (polling every {WORKER_POLL_INTERVAL}s)")

        while self.running:
            try:
                tasks = get_pending_tasks(limit=10)

                if tasks:
                    logger.info(f"[WORKER] found {len(tasks)} pending tasks")

                    for share_id in tasks:
                        if not self.running:
                            break
                        await self.process_task(share_id)
                else:
                    logger.debug("[WORKER] no pending tasks")

                await asyncio.sleep(WORKER_POLL_INTERVAL)

            except Exception as e:
                logger.error(f"[WORKER] error: {e}")
                await asyncio.sleep(WORKER_POLL_INTERVAL)

    def stop(self):
        logger.info("Worker stopping...")
        self.running = False
