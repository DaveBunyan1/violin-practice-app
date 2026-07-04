from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends

from app.core.logging import logger
from app.core.runtime import RuntimeGraph
from app.dependencies.runtime import get_runtime

router = APIRouter()


@router.websocket("/stream")
async def websocket_stream_endpoint(
    websocket: WebSocket,
    runtime: RuntimeGraph = Depends(get_runtime),
):
    """
    Accepts incoming telemetry connections and streams real-time
    note and pitch error updates to the client.
    """
    await websocket.accept()
    logger.info("Client connected to live telemetry stream.")

    event_queue = await runtime.event_bus.subscribe()

    try:
        while True:
            event = await event_queue.get()

            await websocket.send_json(event)

    except WebSocketDisconnect:
        logger.info("Client disconnected from telemetry stream.")

    finally:
        # Clean up subscription
        await runtime.event_bus.unsubscribe(event_queue)
