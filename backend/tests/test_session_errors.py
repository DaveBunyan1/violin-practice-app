from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import RepertoirePiece


def test_start_session_fails_if_already_running(
    client: TestClient, db_session: Session
):
    target_piece = RepertoirePiece(
        title="Error Test Piece",
        total_duration=60.0,
        bpm=120,
        time_signature_numerator=4,
    )

    db_session.add(target_piece)
    db_session.commit()
    db_session.refresh(target_piece)

    payload = {
        "piece_id": target_piece.id,
        "start_bar": 1,
        "end_bar": 16,
        "target_bpm": 100,
        "countdownSeconds": 3,
    }

    # Start it once successfully
    client.post("/session/start", json=payload)

    # 🌟 Try starting a second one simultaneously to trigger lines 29-30
    response = client.post("/session/start", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Session is already actively running."

    # Clean up state for other tests
    client.post("/session/end")


def test_start_session_invalid_piece_returns_404(client: TestClient):
    # 🌟 Pass a piece_id that doesn't exist in the DB to trigger lines 43-44
    payload = {
        "piece_id": 9999,
        "start_bar": 1,
        "end_bar": 16,
        "target_bpm": 100,
        "countdownSeconds": 3,
    }
    response = client.post("/session/start", json=payload)
    assert response.status_code == 404
