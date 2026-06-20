import asyncio
import json
import os
import queue
from typing import Any, Callable, Coroutine, Dict
from dotenv import load_dotenv

import websockets
from websockets.asyncio.server import ServerConnection

from app.models.session_controller import SessionController
from app.core.events import WebSocketBroadcastEvent
from app.scoring.scoring_engine import ScoreEngine

# ---------------------------------------------------
# 1. Configuration & Global State
# ---------------------------------------------------
load_dotenv()

HOST = os.getenv("WEBSOCKET_HOST", "localhost")
PORT = int(os.getenv("WEBSOCKET_PORT", 9999))

connected_clients: set[ServerConnection] = set()


# ---------------------------------------------------
# 2. Inbound Message Handler Factory
# ---------------------------------------------------
def create_handler(
    controller: SessionController, score_engine: ScoreEngine
) -> Callable[[ServerConnection], Coroutine[Any, Any, None]]:
    async def handler(websocket: ServerConnection) -> None:
        print(f"Client connected: {websocket.remote_address}")
        connected_clients.add(websocket)

        try:
            async for message in websocket:
                try:
                    data: Dict[str, Any] = json.loads(message)
                    msg_type = data.get("type")

                    # Handle frontend events
                    if msg_type == "start_session":
                        controller.start_session()
                        print("Session started via frontend request.")
                    elif msg_type == "reset_session":
                        controller.reset_session()
                        print("Session reset via frontend request.")

                    elif msg_type == "end_session":
                        controller.end_session()
                        score = score_engine.compute()

                        await websocket.send(
                            json.dumps({"type": "score_result", "data": score})
                        )
                    else:
                        print(f"Unhandled WebSocket message type: {msg_type}")

                except json.JSONDecodeError:
                    print("Received malformed, non-JSON payload from client.")

        except Exception as e:
            print(f"WebSocket connection error: {e}")
        finally:
            connected_clients.discard(websocket)
            print("Client disconnected.")

    return handler


# ---------------------------------------------------
# 3. Outbound Broadcaster Loop
# ---------------------------------------------------
async def broadcaster(broadcast_queue: queue.Queue[WebSocketBroadcastEvent]):
    """
    Pulls fully processed pitch/expected events from the pipeline thread
    and concurrent-broadcasts them to all listening WebSocket clients.
    """
    while True:
        event = await asyncio.to_thread(broadcast_queue.get)

        msg = json.dumps(event)

        if connected_clients:
            await asyncio.gather(
                *[ws.send(msg) for ws in connected_clients], return_exceptions=True
            )


# ---------------------------------------------------
# 4. Server Lifecycle Runner
# ---------------------------------------------------
async def run(
    handler: Callable[[ServerConnection], Coroutine[Any, Any, None]],
    broadcaster_task_factory: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """
    Starts the WebSocket server and pins the background broadcaster loop open.
    """
    print(f"Starting WebSocket server on {HOST}:{PORT}...")

    async with websockets.serve(handler, HOST, PORT):
        print("WebSocket server is actively accepting connections.")

        # Fire off the broadcaster coroutine via its factory and suspend forever
        await asyncio.gather(
            broadcaster_task_factory(), asyncio.Future()  # Keeps server process alive
        )
