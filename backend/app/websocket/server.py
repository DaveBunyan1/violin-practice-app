import asyncio
import websockets
from websockets.asyncio.server import ServerConnection
from dotenv import load_dotenv
import os

from audio.record import note_queue

load_dotenv()

HOST = os.getenv("WEBSOCKET_HOST", "localhost")
PORT = int(os.getenv("WEBSOCKET_PORT", 9999))


async def hello(websocket: ServerConnection):
    name = await websocket.recv()
    print(f"Server received: {name}")
    greeting = f"Hello, {name}"

    await websocket.send(greeting)
    print(f"Server sent: {greeting}")


async def broadcast_pitch(websocket: ServerConnection):
    while True:
        freq, note = await asyncio.to_thread(note_queue.get)
        msg = f"{freq:.2f} Hz → {note}"
        await websocket.send(msg)


async def test():
    print(f"Starting WebSocket server on {HOST}:{PORT}...")
    async with websockets.serve(hello, HOST, PORT):
        print("WebSocket server is accepting connections")
        await asyncio.Future()


async def run():
    print(f"Starting WebSocket server on {HOST}:{PORT}...")
    async with websockets.serve(broadcast_pitch, HOST, PORT):
        print("WebSocket server is accepting connections")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(test())
