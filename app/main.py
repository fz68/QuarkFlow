import asyncio
import logging
import threading
from app.telegram.listener import TelegramListener
from app.tasks.worker import QuarkWorker
from app.db import init_db
from app.web.app import run_web_server

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting QuarkFlow...")

    init_db()
    logger.info("Database initialized")

    web_thread = threading.Thread(
        target=run_web_server, kwargs={"host": "0.0.0.0", "port": 8080}, daemon=True
    )
    web_thread.start()
    logger.info("WebUI started on http://0.0.0.0:8080")

    listener = TelegramListener()
    worker = QuarkWorker()

    try:
        await listener.start()

        worker_task = asyncio.create_task(worker.run())

        await listener.listen()

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        worker.stop()
        await listener.stop()
        try:
            await asyncio.wait_for(worker_task, timeout=5)
        except asyncio.TimeoutError:
            logger.warning("Worker did not stop gracefully")


if __name__ == "__main__":
    asyncio.run(main())
