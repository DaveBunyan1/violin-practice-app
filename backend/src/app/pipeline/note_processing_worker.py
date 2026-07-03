import queue
import threading
from enum import Enum, auto

from app.controllers.session_controller import SessionController
from app.models.events import (
    PerformedNoteEvent,
    LiveDashboardMetrics,
    WebSocketBroadcastEvent,
)
from app.core.logging import logger

MAX_RETRIES = 3


class ProcessResult(Enum):
    OK = auto()
    RETRY = auto()
    DROP = auto()


class NoteProcessingWorker:
    def __init__(
        self,
        controller: SessionController,
        inbound_queue: queue.Queue[PerformedNoteEvent],
        websocket_broadcast_queue: queue.Queue[WebSocketBroadcastEvent],
        retry_queue: queue.Queue[PerformedNoteEvent],
        dead_letter_queue: queue.Queue[PerformedNoteEvent],
    ) -> None:
        self.controller = controller
        self.inbound_queue = inbound_queue
        self.websocket_broadcast_queue = websocket_broadcast_queue
        self._stop_event = threading.Event()
        self.retry_queue = retry_queue
        self.dead_letter_queue = dead_letter_queue

    def stop(self) -> None:
        """Signals the background loop to shut down gracefully."""
        self._stop_event.set()

    @property
    def is_running(self) -> bool:
        return not self._stop_event.is_set()

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
                    event["retry_count"] = event.get("retry_count", 0) + 1

                    if event["retry_count"] > MAX_RETRIES:
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

                elif result == ProcessResult.DROP:
                    self.dead_letter_queue.put(event)

                    logger.error(
                        "event_dropped",
                        extra={"extra_context": {"event": event}},
                    )

            finally:
                self.inbound_queue.task_done()

    def _process_single_event(self, event: PerformedNoteEvent) -> ProcessResult:
        """Handles the normalization, tracking, and transformation logic for an event."""
        event.setdefault("retry_count", 0)
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

        # 1. Normalize time (single source of truth)
        session_start = session.start_time

        relative_start = event["start_time"] - session_start
        relative_end = event["end_time"] - session_start

        # 2. Expected note lookup (time-based)
        try:
            expected = self.controller.target.get_expected_note(relative_start)
        except Exception:
            return ProcessResult.RETRY
        avg_cents = event.get("avg_pitch_error_cents")

        # 3. Session event (clean storage format)
        try:
            session.add_performed_note(
                {
                    "note": event["note"],
                    "frequency": event["frequency"],
                    "start_time": relative_start,
                    "end_time": relative_end,
                    "duration": event["duration"],
                    "avg_pitch_error_cents": event.get("avg_pitch_error_cents"),
                }
            )
        except Exception:
            return ProcessResult.RETRY

        # 4. Live UI metrics transformation
        metrics: LiveDashboardMetrics = {
            "frequency": event["frequency"],
            "note": event["note"],
            "time": relative_start,
            "expected_note": expected,
            "pitch_cents_error": avg_cents,
        }

        # 5. Push to WebSocket output queue
        try:
            self.websocket_broadcast_queue.put(
                {
                    "type": "pitch",
                    "data": metrics,
                }
            )
        except Exception:
            return ProcessResult.RETRY

        return ProcessResult.OK
