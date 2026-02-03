import asyncio
import logging
from app.db import get_pending_tasks, mark_share_saved, mark_share_failed
from app.config import WORKER_POLL_INTERVAL, WORKER_CONCURRENT_TASKS
from app.quark.client import QuarkClient

logger = logging.getLogger(__name__)


class QuarkWorker:
    def __init__(self):
        from app.config import BX_UA, BX_UMIDTOKEN

        self.semaphore = asyncio.Semaphore(WORKER_CONCURRENT_TASKS)
        self.running = False
        self.quark_client = QuarkClient(bx_ua=BX_UA, bx_umidtoken=BX_UMIDTOKEN)

    async def process_task(self, share_id: str):
        async with self.semaphore:
            logger.info(f"[WORKER] processing share_id={share_id}")

            try:
                result = await self.quark_client.save_share(share_id=share_id)

                if result["success"]:
                    task_id = result.get("task_id", "")
                    logger.info(f"[WORKER] done, status=saved, task_id={task_id}")
                    mark_share_saved(share_id, task_id)
                else:
                    error = result.get("error", "Unknown error")
                    logger.error(f"[WORKER] failed for share_id={share_id}: {error}")
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
