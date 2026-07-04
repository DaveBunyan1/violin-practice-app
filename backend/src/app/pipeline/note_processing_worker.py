import asyncio
import queue
import threading
from enum import Enum, auto

from app.controllers.session_controller import SessionController
from app.core.event_bus import EventBus
from app.models.events import (
    PerformedNoteEvent,
    LiveDashboardMetrics,
)
from app.core.logging import logger
from app.core.config import settings


class ProcessResult(Enum):
    OK = auto()
    RETRY = auto()
    DROP = auto()


class NoteProcessingWorker:
    def __init__(
        self,
        controller: SessionController,
        inbound_queue: queue.Queue[PerformedNoteEvent],
        event_bus: EventBus,
        retry_queue: queue.Queue[PerformedNoteEvent],
        dead_letter_queue: queue.Queue[PerformedNoteEvent],
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self.controller = controller
        self.inbound_queue = inbound_queue
        self.event_bus = event_bus

        self.retry_queue = retry_queue
        self.dead_letter_queue = dead_letter_queue

        self.loop = loop
        self._stop_event = threading.Event()

    # ----------------------------
    # Lifecycle
    # ----------------------------
    def stop(self) -> None:
        """Signals the background loop to shut down gracefully."""
        self._stop_event.set()

    @property
    def is_running(self) -> bool:
        return not self._stop_event.is_set()

    # ----------------------------
    # Main worker loop
    # ----------------------------
    def run(self) -> None:
        """
        Worker Loop:
        Pulls PerformedNoteEvents, processes them against the active session,
        and broadcasts live metrics to the WebSocket output queue.
        """
        while self.is_running:
            try:
                event = self.inbound_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                result = self._process_single_event(event)

                if result == ProcessResult.RETRY:
                    self._handle_retry(event)

                elif result == ProcessResult.DROP:
                    self._handle_drop(event)

            finally:
                self.inbound_queue.task_done()

    # ----------------------------
    # Retry / Drop handling
    # ----------------------------
    def _handle_retry(self, event: PerformedNoteEvent) -> None:
        event["retry_count"] = event.get("retry_count", 0) + 1

        if event["retry_count"] > settings.MAX_RETRIES:
            logger.error(
                "event_dead_lettered_max_retries",
                extra={"extra_context": {"event": event}},
            )
            self.dead_letter_queue.put(event)
        else:
            self.retry_queue.put(event)

            logger.warning(
                "event_retried",
                extra={"extra_context": {"event": event}},
            )

    def _handle_drop(self, event: PerformedNoteEvent) -> None:
        self.dead_letter_queue.put(event)

        logger.error(
            "event_dropped",
            extra={"extra_context": {"event": event}},
        )

    # ----------------------------
    # Core processing
    # ----------------------------
    def _process_single_event(self, event: PerformedNoteEvent) -> ProcessResult:
        """Handles the normalization, tracking, and transformation logic for an event."""
        try:
            if not self.controller.is_active():
                return ProcessResult.DROP

            session = self.controller.get_session()

        except RuntimeError as e:
            logger.warning(
                "session_error",
                extra={"extra_context": {"event": event, "error": str(e)}},
            )
            return ProcessResult.RETRY

        telemetry = event["telemetry"]
        event_id = telemetry["event_id"]
        created_at = telemetry["created_at"]
        # ----------------------------
        # Normalize time
        # ----------------------------
        relative_start = event["start_time"] - session.start_time

        # ----------------------------
        # Expected note lookup
        # ----------------------------
        try:
            if not self.controller.target:
                return ProcessResult.RETRY

            expected = self.controller.target.get_expected_note(relative_start)

        except Exception as e:
            logger.warning(
                "expected_note_lookup_failed",
                extra={"extra_context": {"error": str(e)}},
            )
            return ProcessResult.RETRY

        avg_cents = event.get("avg_pitch_error_cents")

        # ----------------------------
        # Persist to session
        # ----------------------------
        try:
            session.add_performed_note(
                {
                    "note": event["note"],
                    "start_time": relative_start,
                    "duration": event["duration"],
                    "avg_pitch_error_cents": avg_cents,
                }
            )
        except Exception as e:
            logger.warning(
                "session_persistence_failed",
                extra={"extra_context": {"error": str(e)}},
            )
            return ProcessResult.RETRY

        # ----------------------------
        # Build live metrics
        # ----------------------------
        metrics: LiveDashboardMetrics = {
            "frequency": event["frequency"],
            "note": event["note"],
            "time": relative_start,
            "expected_note": expected,
            "pitch_cents_error": avg_cents,
        }

        # ----------------------------
        # Emit to event bus
        # ----------------------------
        self._emit(metrics, event_id, created_at)

        return ProcessResult.OK

    def _emit(
        self, metrics: LiveDashboardMetrics, event_id: str, created_at: float
    ) -> None:
        asyncio.run_coroutine_threadsafe(
            self.event_bus.publish(
                {
                    "type": "pitch",
                    "data": metrics,
                    "telemetry": {"event_id": event_id, "created_at": created_at},
                },
            ),
            self.loop,
        )
