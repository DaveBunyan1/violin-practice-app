import sounddevice as sd  # type: ignore
from scipy.io.wavfile import write


def record_violin(file_name: str, duration: int = 5, sample_rate: int = 44100):
    print(f"Recording for {duration} seconds...")
    audio_data = sd.rec(
        int(sample_rate * duration), samplerate=sample_rate, channels=2, dtype="int16"
    )
    sd.wait()
    write(file_name, sample_rate, audio_data)
    print(f"Recording saved to {file_name}")


if __name__ == "__main__":
    record_violin("e-output.wav", duration=5)
    print("Audio recording complete.")
