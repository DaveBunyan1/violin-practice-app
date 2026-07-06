import numpy as np
import scipy.io.wavfile as wavfile


def generate_g_melodic_minor_scale(
    filename: str = "tests/benchmarks/continuous_practice_recording.wav",
    sr: int = 44100,
    note_duration: float = 0.5,
):
    # Frequencies for G Melodic Minor (Starting at G4 ~392Hz up to G5 ~784Hz)
    # Ascending: G4, A4, Bb4, C5, D5, E5, F#5, G5
    ascending_freqs = [392.00, 440.00, 466.16, 523.25, 587.33, 659.25, 739.99, 783.99]
    # Descending: F5, Eb5, D5, C5, Bb4, A4, G4
    descending_freqs = [698.46, 622.25, 587.33, 523.25, 466.16, 440.00, 392.00]

    scale_freqs = ascending_freqs + descending_freqs
    total_samples_per_note = int(sr * note_duration)
    t_note = np.linspace(0, note_duration, total_samples_per_note, endpoint=False)

    full_signal = []

    for freq in scale_freqs:
        # Build composite violin timbre profile for each note step
        note_signal = (
            1.000 * np.sin(2 * np.pi * freq * t_note)  # Fundamental
            + 0.263 * np.sin(2 * np.pi * (freq * 2) * t_note)  # 2nd Harmonic
            + 0.140 * np.sin(2 * np.pi * (freq * 3) * t_note)  # 3rd Harmonic
        )
        # Apply a micro-fade window at the very edge of notes to simulate clean transitions
        fade_size = int(sr * 0.01)  # 10ms crossfade buffer
        window = np.ones(total_samples_per_note, dtype=np.float32)
        window[:fade_size] = np.linspace(0, 1, fade_size)
        window[-fade_size:] = np.linspace(1, 0, fade_size)

        full_signal.append(note_signal * window)

    # Flatten array strings and normalize
    combined_audio = np.concatenate(full_signal)
    normalized = (combined_audio / np.max(np.abs(combined_audio)) * 32767).astype(
        np.int16
    )

    wavfile.write(filename, sr, normalized)
    print(
        f"🎻 G Melodic Minor Scale generated successfully ({len(scale_freqs)} total note events)."
    )


if __name__ == "__main__":
    generate_g_melodic_minor_scale()
