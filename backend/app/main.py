from audio.record import record_violin
from pitch.autocorrelation import estimate_frequency
from pitch.notes import freq_to_note


if __name__ == "__main__":
    audio_data, sample_rate = record_violin(duration=5)
    freq = estimate_frequency(audio_data, sample_rate)
    note = freq_to_note(freq)
    print(f"Estimated frequency: {freq:.2f} Hz → {note}")
