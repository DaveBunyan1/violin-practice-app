import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Replace with your actual model imports
from app.pipeline.ingestion import AudioIngestionStream
from tests.utils.audio_harness import AudioStreamTestHarness
from app.database.models import RepertoireNote, RepertoirePiece


def test_full_session_lifecycle_integration(
    client: TestClient,
    db_session: Session,
    audio_harness: tuple[AudioStreamTestHarness, AudioIngestionStream],
):
    """
    Integration Test:
    1. Seeds a piece of music into the test DB.
    2. Starts a practice session via HTTP POST.
    3. Simulates a student playing an A4 note using the audio test harness.
    4. Finishes the session via HTTP POST and verifies the final generated score.
    """
    harness, _ = audio_harness

    # --- PHASE 1: Seed Practice Target Data ---
    target_piece = RepertoirePiece(
        title="Violin Concerto in A minor",
        total_duration=120.0,
        bpm=100,
        time_signature_numerator=4,
    )

    target_piece.notes = [
        RepertoireNote(note="A4", time=0.0, duration=0.5),
        RepertoireNote(note="E5", time=0.5, duration=0.5),
    ]
    db_session.add(target_piece)
    db_session.commit()
    db_session.refresh(target_piece)

    # --- PHASE 2: Start the Practice Session via API ---
    # Provide every required field for StartSessionPayload
    start_payload = {
        "piece_id": target_piece.id,
        "start_bar": 1,
        "end_bar": 16,
        "target_bpm": 100,
        "countdownSeconds": 3,
    }

    start_response = client.post("/session/start", json=start_payload)
    assert start_response.status_code == 200

    session_data = start_response.json()
    assert session_data["session_active"] is True

    # --- PHASE 3: Stream Audio Buffer Blocks via Harness ---
    dummy_audio_chunk = np.zeros((256, 1), dtype=np.float32)
    mock_frames = [
        (0.00, dummy_audio_chunk),
        (0.05, dummy_audio_chunk),
        (0.11, dummy_audio_chunk),
        (0.22, dummy_audio_chunk),
    ]
    harness.feed(mock_frames)

    # --- PHASE 4: Finalize & Score the Session via API ---
    # Route updated to your precise static path string: "/session/end"
    stop_response = client.post("/session/end")

    assert stop_response.status_code == 200
    report = stop_response.json()

    # --- PHASE 5: Verify Response Schema Match ---
    assert "message" in report
    assert "database_id" in report
    assert "score_result" in report
