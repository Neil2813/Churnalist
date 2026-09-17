"""
Background task manager for analysis pipeline runs.

For the hackathon, this is an in-process async task manager.
It can be replaced with Celery/Arq without changing domain services.
"""
from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskManager:
    """
    Simple in-process task manager for background analysis runs.

    Tracks running tasks by run_id so we can:
    - prevent duplicate runs
    - check cancellation between pipeline stages
    - cleanly await all tasks on shutdown
    """

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}

    def submit(self, run_id: str, coro: Coroutine[Any, Any, Any]) -> asyncio.Task:
        """
        Schedule a coroutine as a background task.

        Returns the asyncio.Task immediately; the coroutine runs concurrently.
        """
        if run_id in self._tasks and not self._tasks[run_id].done():
            logger.warning("task_already_running", run_id=run_id)
            return self._tasks[run_id]

        task = asyncio.create_task(coro, name=f"run-{run_id}")
        self._tasks[run_id] = task

        def _cleanup(t: asyncio.Task) -> None:
            self._tasks.pop(run_id, None)
            if t.exception():
                logger.error("task_failed", run_id=run_id, exc_info=t.exception())

        task.add_done_callback(_cleanup)
        logger.info("task_submitted", run_id=run_id)
        return task

    def cancel(self, run_id: str) -> bool:
        """Cancel a running task by run_id. Returns True if cancelled."""
        task = self._tasks.get(run_id)
        if task and not task.done():
            task.cancel()
            logger.info("task_cancelled", run_id=run_id)
            return True
        return False

    def is_running(self, run_id: str) -> bool:
        task = self._tasks.get(run_id)
        return task is not None and not task.done()

    async def shutdown(self) -> None:
        """Cancel all running tasks and await them during shutdown."""
        running = [t for t in self._tasks.values() if not t.done()]
        for task in running:
            task.cancel()
        if running:
            await asyncio.gather(*running, return_exceptions=True)
        logger.info("task_manager_shutdown", cancelled=len(running))
