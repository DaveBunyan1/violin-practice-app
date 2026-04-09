from audio.record import start_audio_stream
from websocket.server import run as run_server
import threading
import asyncio


async def main():
    threading.Thread(target=start_audio_stream, daemon=True).start()

    await run_server()


if __name__ == "__main__":
    asyncio.run(main())
