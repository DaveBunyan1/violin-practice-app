import queue

from app.models.events import PitchObservationEvent
from app.core.logging import logger
from app.core.shared_engines import segmenter


def run_segmentation_pipeline(
    inbound_raw_queue: queue.Queue[PitchObservationEvent],
) -> None:
    """Worker Loop Thread: Pulls raw observations and passes them to the segmenter."""
    logger.info("Segmentation background thread worker started.")

    while True:
        try:
            raw_event = inbound_raw_queue.get(timeout=1.0)

            logger.debug(
                f"Processing raw frame: {raw_event['note']}",
                extra={
                    "extra_context": {
                        "frequency": round(raw_event["frequency"], 1),
                        "pitch_cents_error": raw_event.get("pitch_cents_error"),
                    }
                },
            )
            segmenter.process(raw_event)
            inbound_raw_queue.task_done()
        except queue.Empty:
            continue
        except Exception:
            logger.error(
                "Segmentation thread encountered a critical error.", exc_info=True
            )
