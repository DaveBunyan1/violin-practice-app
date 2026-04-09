import asyncio
import websockets
from dotenv import load_dotenv
import os


load_dotenv()

HOST = os.getenv("WEBSOCKET_HOST", "localhost")
PORT = int(os.getenv("WEBSOCKET_PORT", 9999))


async def hello():
    uri = f"ws://{HOST}:{PORT}"
    async with websockets.connect(uri) as websocket:
        name = input("What is your name: ")

        await websocket.send(name)
        print(f"Client sent: {name}")

        msg = await websocket.recv()
        print(f"Client received: {msg}")


async def listen():
    uri = f"ws://{HOST}:{PORT}"
    async with websockets.connect(uri) as websocket:
        while True:
            msg = await websocket.recv()
            print(msg)


if __name__ == "__main__":
    asyncio.run(listen())
