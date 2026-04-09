import sounddevice as sd  # type: ignore
from audio.record import start_audio_stream
from server.server import run as run_server
import threading


SAMPLE_RATE = 44100
BUFFER_SIZE = 2048  # number of samples per chunk
CHANNELS = 1

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    threading.Thread(target=start_audio_stream).start()
