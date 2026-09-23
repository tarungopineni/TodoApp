import asyncio
import logging
from typing import Optional
from TodoApp.database import SessionLocal
from TodoApp.services.reminder_service import process_reminders

logger = logging.getLogger("reminder_scheduler")

class ReminderScheduler:
    def __init__(self, interval_seconds: int = 60):
        self.interval_seconds = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._lock = asyncio.Lock()

    def start(self):
        if self._running:
            return

        self._running = True
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._run_loop())
            logger.info("Deadline reminder scheduler started.")
        except RuntimeError:
            logger.warning("No running asyncio event loop found during scheduler start.")

    async def _run_loop(self):
        while self._running:
            try:
                if not self._lock.locked():
                    async with self._lock:
                        await asyncio.to_thread(self._execute_check)
            except asyncio.CancelledError:
                logger.info("Deadline reminder scheduler task cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in deadline reminder scheduler loop: {e}")

            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                logger.info("Deadline reminder scheduler sleep cancelled.")
                break

    def _execute_check(self):
        db = SessionLocal()
        try:
            process_reminders(db)
        except Exception as e:
            logger.error(f"Error executing reminder check: {e}")
        finally:
            db.close()

    async def stop(self):
        if not self._running:
            return

        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Deadline reminder scheduler stopped.")

reminder_scheduler = ReminderScheduler(interval_seconds=60)
