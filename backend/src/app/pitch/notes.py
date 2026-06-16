import numpy as np


def freq_to_note(freq: float) -> str:
    if freq <= 0:
        return "Unknown"

    A4 = 440.0
    n = int(round(12 * np.log2(freq / A4)))

    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]

    index = (n + 9) % 12  # A = 9
    octave = 4 + ((n + 9) // 12)

    return f"{notes[index]}{octave}"
