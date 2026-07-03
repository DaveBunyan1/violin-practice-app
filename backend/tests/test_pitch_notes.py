from app.pitch.notes import freq_to_note, calculate_pitch_error


def test_freq_to_note_handles_zero_or_negative_frequencies():
    # 🌟 Triggers line 9
    assert freq_to_note(0.0) == "Unknown"
    assert freq_to_note(-440.0) == "Unknown"


def test_calculate_pitch_error_handles_zero_or_negative_frequencies():
    # 🌟 Triggers line 27
    assert calculate_pitch_error(0.0) == 0.0
    assert calculate_pitch_error(-100.0) == 0.0


def test_pitch_utilities_happy_path():
    # Verify standard functional calculations work accurately
    assert freq_to_note(440.0) == "A4"

    # 443.0 Hz is slightly sharp of A4
    assert calculate_pitch_error(443.0) > 0.0
