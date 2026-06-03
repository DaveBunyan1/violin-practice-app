import asyncio
import websockets
from websockets.asyncio.server import ServerConnection
from dotenv import load_dotenv
import os
import json


from models.session import session
from core.events import note_queue

load_dotenv()

HOST = os.getenv("WEBSOCKET_HOST", "localhost")
PORT = int(os.getenv("WEBSOCKET_PORT", 9999))

connected_clients: set[ServerConnection] = set()


async def handler(websocket: ServerConnection):
    print("Client connected.")
    connected_clients.add(websocket)

    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print("Client disconnected.")


async def broadcaster():
    while True:
        event = await asyncio.to_thread(note_queue.get)

        msg = json.dumps(
            {
                "type": "pitch",
                "data": {
                    "frequency": event["frequency"],
                    "note": event["note"],
                    "time": event["timestamp"] - session.start_time,
                },
            }
        )

        if connected_clients:
            await asyncio.gather(
                *[ws.send(msg) for ws in connected_clients], return_exceptions=True
            )


async def run():
    print(f"Starting WebSocket server on {HOST}:{PORT}...")

    async with websockets.serve(handler, HOST, PORT):
        print("WebSocket server is accepting connections")

        await asyncio.gather(broadcaster(), asyncio.Future())
