import asyncio
import time


from app.core.event_bus import EventBus
from app.models.events import WebSocketBroadcastEvent
from app.benchmarks.latency_collector import LatencyCollector

collector = LatencyCollector()


async def consume(
    bus_queue: asyncio.Queue[WebSocketBroadcastEvent], n: int, label: str
):
    for _ in range(n):
        event = await bus_queue.get()

        created = event["telemetry"]["created_at"]
        now = time.perf_counter()

        collector.record(label, (now - created) * 1000)


async def run_event_bus_test(n: int = 1000):
    event_bus = EventBus()

    queue = await event_bus.subscribe()

    consumer_task = asyncio.create_task(consume(queue, n, "event_bus_latency"))

    # -------------------------
    # producer (your system)
    # -------------------------
    for i in range(n):
        print("Iteration:", i)
        now = time.perf_counter()

        event: WebSocketBroadcastEvent = {
            "type": "pitch",
            "data": {
                "frequency": 440.0,
                "note": "A4",
                "time": now,
                "expected_note": "A4",
                "pitch_cents_error": 0.0,
            },
            "telemetry": {
                "event_id": f"test-{i}",
                "created_at": now,
            },
        }

        await event_bus.publish(event)

    await consumer_task

    return collector.summary("event_bus_latency")


if __name__ == "__main__":
    result = asyncio.run(run_event_bus_test(1000))
    print(result)
