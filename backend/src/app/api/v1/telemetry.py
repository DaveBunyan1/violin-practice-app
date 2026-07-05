import asyncio
import queue
import time

from fastapi import Depends, WebSocket, WebSocketDisconnect, APIRouter

from app.core.logging import logger
from app.core.runtime import RuntimeGraph
from app.dependencies.runtime import get_runtime

router = APIRouter()


@router.websocket("/stream")
async def websocket_stream_endpoint(
    websocket: WebSocket, runtime: RuntimeGraph = Depends(get_runtime)
):
    """
    Accepts incoming telemetry connections and streams real-time
    note and pitch error updates to the client.
    """
    await websocket.accept()
    logger.info("Client connected to live telemetry stream.")

    try:
        while True:
            # Check the broadcast queue for pipeline events without blocking the async loop.
            # Using asyncio.sleep allows other network connections to share resources smoothly.
            try:
                # Get the event from Thread C's queue output
                event, trace = runtime.broadcast_queue.get_nowait()
                print("In websocket:", event, trace)

                if trace:
                    trace["t_websocket"] = time.perf_counter()
                    print("WS trace:", trace)
                    runtime.telemetry.complete_trace(trace)

                # Send it over the active WebSocket network channel
                await websocket.send_json(event)
                runtime.broadcast_queue.task_done()

            except queue.Empty:
                # If no data is ready, yield control back to the async engine for a brief moment
                await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        logger.info("Client disconnected from live telemetry stream.")
