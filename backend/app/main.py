import sounddevice as sd  # type: ignore
from audio.record import audio_callback


SAMPLE_RATE = 44100
BUFFER_SIZE = 2048  # number of samples per chunk
CHANNELS = 1

if __name__ == "__main__":
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        blocksize=BUFFER_SIZE,
        callback=audio_callback,
    ):
        print("Real-time pitch detection started. Press Ctrl+C to stop.")
        try:
            # Keep the stream alive
            while True:
                sd.sleep(1000)  # type: ignore
        except KeyboardInterrupt:
            print("\nStopping real-time detection.")
