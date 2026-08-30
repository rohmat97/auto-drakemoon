"""
session_scheduler.py — Modular Session and Cooldown Lifecycle Manager.

Provides a robust, reusable scheduler for managing long-running tasks,
enforcing periodic rest/cooldown intervals based on iteration limits or elapsed time.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple, Union

# Configure module-level logger
logger = logging.getLogger("SessionScheduler")


@dataclass
class SessionConfig:
    """Configuration options for a SessionScheduler."""

    # Iteration limits (fixed int or (min, max) tuple for randomized batches)
    max_iterations: Union[int, Tuple[int, int]] = (100, 150)

    # Session duration in seconds (fixed float or (min, max) tuple for randomized duration)
    max_duration_seconds: Union[float, Tuple[float, float]] = (60.0 * 60, 120.0 * 60)

    # Cooldown / break duration in seconds (fixed float or (min, max) tuple)
    cooldown_seconds: Union[float, Tuple[float, float]] = (5.0 * 60, 10.0 * 60)

    # Interval delay between main task loop iterations (seconds)
    loop_interval_seconds: float = 0.15

    # Check interval step during long cooldown sleeps to ensure responsive shutdown (seconds)
    cooldown_step_seconds: float = 1.0


class SessionScheduler:
    """
    Manages the lifecycle of a recurring task with automated cooldown intervals.

    Attributes:
        config (SessionConfig): The scheduling parameters.
        task_func (Callable[[], Any]): The main task executed on each loop cycle.
        cooldown_func (Optional[Callable[[str, int, float], Any]]): Optional callback
            executed at the start of cooldown (receives trigger reason, iterations, elapsed).
        pause_check (Optional[Callable[[], bool]]): Optional predicate to check if task is paused.
    """

    def __init__(
        self,
        task_func: Callable[[], Any],
        cooldown_func: Optional[Callable[[str, int, float], Any]] = None,
        pause_check: Optional[Callable[[], bool]] = None,
        config: Optional[SessionConfig] = None,
    ) -> None:
        self.task_func = task_func
        self.cooldown_func = cooldown_func
        self.pause_check = pause_check
        self.config = config or SessionConfig()

        self._stop_event = threading.Event()
        self._is_running = False

        # Session metrics
        self.session_index: int = 0
        self.current_iteration: int = 0
        self.total_iterations: int = 0
        self.session_start_time: float = 0.0

        # Current targets
        self._target_iterations: int = 0
        self._target_duration: float = 0.0

    @staticmethod
    def _resolve_value(val: Union[int, float, Tuple[int, int], Tuple[float, float]]) -> float:
        """Resolve a fixed or ranged (min, max) configuration value."""
        if isinstance(val, (tuple, list)):
            return random.uniform(val[0], val[1]) if isinstance(val[0], float) else random.randint(val[0], val[1])
        return float(val)

    def _reset_session_targets(self) -> None:
        """Initialize or reset session counters and randomize new targets."""
        self.current_iteration = 0
        self.session_start_time = time.time()
        self._target_iterations = int(self._resolve_value(self.config.max_iterations))
        self._target_duration = self._resolve_value(self.config.max_duration_seconds)
        self.session_index += 1

        logger.info(
            f"[Session #{self.session_index}] Started | Next Cooldown Target: "
            f"{self._target_iterations} iterations OR {self._target_duration / 60:.1f} minutes"
        )

    def _should_trigger_cooldown(self) -> Tuple[bool, str]:
        """Check if iteration threshold or time duration has been reached."""
        elapsed = time.time() - self.session_start_time
        if self.current_iteration >= self._target_iterations:
            return True, f"Reached iteration target ({self.current_iteration}/{self._target_iterations})"
        if elapsed >= self._target_duration:
            return True, f"Elapsed session time limit ({elapsed / 60:.1f}m / {self._target_duration / 60:.1f}m)"
        return False, ""

    def _run_cooldown(self, reason: str) -> None:
        """Executes the cooldown routine and delays execution for the configured duration."""
        elapsed = time.time() - self.session_start_time
        cooldown_duration = self._resolve_value(self.config.cooldown_seconds)

        logger.info("=" * 60)
        logger.info(f"🛑 [Cooldown Triggered] Reason: {reason}")
        logger.info(
            f"   Completed {self.current_iteration} iterations in {elapsed / 60:.1f}m | "
            f"Rest duration: {cooldown_duration / 60:.1f} minutes ({int(cooldown_duration)}s)"
        )
        logger.info("=" * 60)

        # Execute custom cooldown callback if provided
        if self.cooldown_func:
            try:
                self.cooldown_func(reason, self.current_iteration, elapsed)
            except Exception as e:
                logger.error(f"[Cooldown Error] Exception in cooldown callback: {e}", exc_info=True)

        # Responsive sleep loop to allow graceful interruption
        cooldown_start = time.time()
        while not self._stop_event.is_set():
            time_spent = time.time() - cooldown_start
            remaining = cooldown_duration - time_spent
            if remaining <= 0:
                break

            if int(time_spent) % 60 == 0 and int(time_spent) > 0:
                logger.info(f"   [Cooldown Progress] {remaining / 60:.1f} minute(s) remaining...")

            # Sleep in short increments for responsive cancellation
            sleep_chunk = min(self.config.cooldown_step_seconds, max(0.1, remaining))
            time.sleep(sleep_chunk)

        if not self._stop_event.is_set():
            logger.info("✅ [Cooldown Finished] Resuming main task loop.\n")
            self._reset_session_targets()

    def run(self) -> None:
        """
        Starts the continuous scheduling loop.
        Blocks until stop() is called or a KeyboardInterrupt is received.
        """
        self._is_running = True
        self._stop_event.clear()
        self._reset_session_targets()

        logger.info("SessionScheduler loop started.")

        try:
            while not self._stop_event.is_set():
                # 1. Handle external pause state
                if self.pause_check and self.pause_check():
                    time.sleep(0.5)
                    continue

                # 2. Check for Cooldown / Break Triggers
                cooldown_needed, reason = self._should_trigger_cooldown()
                if cooldown_needed:
                    self._run_cooldown(reason)
                    if self._stop_event.is_set():
                        break

                # 3. Execute Primary Task
                try:
                    result = self.task_func()
                    # Only increment iteration on active/truthy task execution (or None)
                    if result is not False:
                        self.current_iteration += 1
                        self.total_iterations += 1
                except Exception as e:
                    logger.error(f"[Task Error] Exception in task loop: {e}", exc_info=True)

                # 4. Pace Loop Iteration
                if self.config.loop_interval_seconds > 0:
                    time.sleep(self.config.loop_interval_seconds)

        except KeyboardInterrupt:
            logger.warning("[SessionScheduler] KeyboardInterrupt caught. Shutting down gracefully...")
        finally:
            self.stop()
            logger.info(
                f"[SessionScheduler] Terminated. Total sessions: {self.session_index}, "
                f"Total iterations: {self.total_iterations}."
            )

    def stop(self) -> None:
        """Signal the scheduler to stop running and exit its loop cleanly."""
        self._is_running = False
        self._stop_event.set()

    @property
    def is_running(self) -> bool:
        """Return True if the scheduler loop is currently active."""
        return self._is_running


# ---------------------------------------------------------------------------
# Usage Demonstration
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # Example 1: Mock task and cooldown functions
    def my_primary_task() -> bool:
        """Simulates doing 1 cycle of work."""
        logger.debug("Executing task step...")
        time.sleep(0.1)
        return True

    def my_cooldown_routine(reason: str, iterations: int, elapsed_sec: float) -> None:
        """Simulates custom cleanup or town activities during cooldown."""
        logger.info(f">> Custom Cooldown Handler: Saving state after {iterations} tasks ({elapsed_sec:.1f}s).")
        logger.info(">> Simulating 2-second quick cleanup before resting...")
        time.sleep(2.0)

    # Example 2: Configure scheduler with short limits for testing
    demo_config = SessionConfig(
        max_iterations=(5, 8),          # Cooldown every 5-8 tasks
        max_duration_seconds=(10, 20),   # Cooldown if duration exceeds 10-20s
        cooldown_seconds=(4, 6),         # 4-6s cooldown rest
        loop_interval_seconds=0.2,
    )

    scheduler = SessionScheduler(
        task_func=my_primary_task,
        cooldown_func=my_cooldown_routine,
        config=demo_config,
    )

    logger.info("Starting demo scheduler (Press Ctrl+C to exit)...")
    try:
        scheduler.run()
    except KeyboardInterrupt:
        scheduler.stop()
