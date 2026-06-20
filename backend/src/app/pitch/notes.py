import numpy as np

A4 = 440.0
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]


def freq_to_note(freq: float) -> str:
    if freq <= 0:
        return "Unknown"

    n = int(round(12 * np.log2(freq / A4)))

    index = (n + 9) % 12  # A = 9
    octave = 4 + ((n + 9) // 12)

    return f"{NOTES[index]}{octave}"


def calculate_pitch_error(freq: float) -> float:
    """
    Calculates how many cents a frequency is away from its nearest
    equal-tempered semitone.

    Returns positive for sharp, negative for flat.
    """
    if freq <= 0:
        return 0.0

    # 1. Find how many semitones away from A4 this frequency is (as a float)
    exact_semitones = 12 * np.log2(freq / A4)

    # 2. Round to the nearest whole semitone (this is the perfect target note)
    nearest_semitone = round(exact_semitones)

    # 3. The difference between exact and nearest semitones is the error in semitones.
    # Multiply by 100 to convert semitones to cents (1 semitone = 100 cents).
    cents_error = (exact_semitones - nearest_semitone) * 100

    return round(cents_error, 1)
