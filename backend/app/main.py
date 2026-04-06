from pitch.autocorrelation import estimate_frequency
from pitch.notes import freq_to_note
from scipy.io.wavfile import read
import numpy as np


if __name__ == "__main__":
    notes_to_test = ["G3.wav", "D4.wav", "A4.wav", "E5.wav"]
    for file in notes_to_test:
        sample_rate, audio_data = read(f"audio/{file}")
        audio_data = audio_data.flatten().astype(np.float32)
        freq = estimate_frequency(audio_data, sample_rate)
        note = freq_to_note(freq)
        print(f"{file}: {freq:.2f} Hz → {note}")
