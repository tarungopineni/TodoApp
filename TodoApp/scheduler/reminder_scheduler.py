import asyncio
import logging
from TodoApp.database import SessionLocal
from TodoApp.services.reminder_service import process_reminders

logger = logging.getLogger(__name__)

class ReminderScheduler:
    def __init__(self, interval_seconds: int = 60):
        self.interval_seconds = interval_seconds
        self._task = None
        self._running = False

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run_loop())
            logger.info("Email scheduler started")

    async def stop(self):
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            logger.info("Email scheduler stopped")

    async def _run_loop(self):
        while self._running:
            try:
                db = SessionLocal()
                try:
                    await asyncio.to_thread(process_reminders, db)
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error in reminder scheduler loop: {e}", exc_info=True)
            
            await asyncio.sleep(self.interval_seconds)

reminder_scheduler = ReminderScheduler(interval_seconds=60)
