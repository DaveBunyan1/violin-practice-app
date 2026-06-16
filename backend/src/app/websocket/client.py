import asyncio
import websockets
from dotenv import load_dotenv
import os
import json


load_dotenv()

HOST = os.getenv("WEBSOCKET_HOST", "localhost")
PORT = int(os.getenv("WEBSOCKET_PORT", 9999))


async def listen():
    uri = f"ws://{HOST}:{PORT}"
    async with websockets.connect(uri) as websocket:
        while True:
            msg = await websocket.recv()
            msg_json = json.loads(msg)

            data = msg_json["data"]

            print(f"{data['time']}: {data['frequency']:.2f} Hz → {data['note']}")


if __name__ == "__main__":
    asyncio.run(listen())
