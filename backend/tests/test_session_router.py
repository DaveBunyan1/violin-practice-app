import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import (
    app,
)
from datetime import datetime, timezone

from app.database import models

client = TestClient(app)


@pytest.fixture
def mock_db_session():
    return MagicMock()


@pytest.fixture
def mock_session_record():
    record = MagicMock()
    record.id = 42
    record.start_time = datetime(2026, 7, 3, 12, 0, tzinfo=timezone.utc)
    record.end_time = datetime(2026, 7, 3, 12, 5, tzinfo=timezone.utc)
    record.piece_id = 1
    record.total_score = 95.5
    record.pitch_accuracy = 98.0
    record.timing_accuracy = 93.0
    record.notes_hit = 10
    record.notes_total = 11

    # Mock nested historical performed notes list
    note = MagicMock()
    note.note = "A4"
    note.avg_pitch_error_cents = 2.3
    note.start_time = 1.5
    note.duration = 0.8
    record.performed_notes = [note]

    return record


def test_get_session_detail_success(mock_session_record: MagicMock):
    """Verifies complete historical object building mapping for full details."""
    with patch(
        "app.api.v1.session.get_session_by_id", return_value=mock_session_record
    ):
        response = client.get("/session/sessions/42")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 42
        assert data["total_score"] == 95.5
        assert len(data["performed_notes"]) == 1
        assert data["performed_notes"][0]["note"] == "A4"


def test_get_session_detail_not_found():
    """Hits the explicit 404 branch check when query yields empty space."""
    with patch("app.api.v1.session.get_session_by_id", return_value=None):
        response = client.get("/session/sessions/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"


def test_get_session_detail_server_error_catch():
    """Forces an internal exception crash to exercise the logger 500 path."""
    with patch(
        "app.api.v1.session.get_session_by_id",
        side_with=Exception("Database connection timed out"),
    ):
        response = client.get("/session/sessions/42")
        assert response.status_code == 500


def test_delete_session_success(client: TestClient, db_session: Session):
    """
    True Integration Test: Seeds a real database row into SQLite,
    fires a client delete request, and verifies it was completely purged.
    """
    # 1. Seed an actual, structurally sound record into the SQLite engine
    test_record = models.SessionRecord(
        id=42,  # Match the target id in our endpoint call
        piece_id=1,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        total_score=88.5,
        pitch_accuracy=90.0,
        timing_accuracy=87.0,
        notes_hit=8,
        notes_total=10,
    )
    db_session.add(test_record)
    db_session.commit()

    # 2. Issue the delete call against our conftest test client
    response = client.delete("/session/42")

    # 3. Assertions
    assert response.status_code == 204

    # 4. Verify it is physically gone from your database engine table
    deleted_check = db_session.query(models.SessionRecord).filter_by(id=42).first()
    assert deleted_check is None


def test_delete_session_not_found():
    """Triggers the logger warning path when attempting to drop an missing record."""
    with patch("app.api.v1.session.get_session_by_id", return_value=None):
        response = client.delete("/session/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"


def test_end_session_no_active_session(client: TestClient):
    response = client.post("/session/end")

    assert response.status_code == 400
    assert response.json()["detail"] == "No active session found to terminate."


def test_end_session_runtime_error(client: TestClient, db_session: Session):
    piece = models.RepertoirePiece(id=1, title="test")
    db_session.add(piece)
    db_session.commit()
    client.post(
        "/session/start",
        json={
            "piece_id": 1,
            "start_bar": 1,
            "end_bar": 10,
            "target_bpm": 80,
            "countdownSeconds": 0,
        },
    )

    with patch("app.api.v1.session.score_engine.compute") as mock_compute:
        mock_compute.side_effect = RuntimeError("boom")

        response = client.post("/session/end")

        assert response.status_code == 400
        assert "Session state error" in response.json()["detail"]


def test_get_session_history_failure(client: TestClient):
    with patch("app.api.v1.session.get_historical_sessions") as mock_service:
        mock_service.side_effect = Exception("DB failure")

        response = client.get("session/sessions?limit=5")

        assert response.status_code == 500
        assert "Database retrieval failed" in response.json()["detail"]


def test_end_session_generic_exception_throws_500(client: TestClient):
    """Forces an unexpected database or core engine crash to cover the 500 branch."""
    # Ensure there is an active session running so it passes the first guard check
    with patch(
        "app.api.v1.session.session_controller.is_active", return_value=True
    ), patch(
        "app.api.v1.session.score_engine.compute",
        side_effect=TypeError("Unexpected analytical type mismatch"),
    ):

        response = client.post("/session/end")
        assert response.status_code == 500
        assert "Scoring calculation failed" in response.json()["detail"]


def test_get_session_history_success(client: TestClient, db_session: Session):
    record = models.SessionRecord(
        id=1,
        piece_id=1,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        total_score=90,
        pitch_accuracy=90,
        timing_accuracy=90,
        notes_hit=10,
        notes_total=10,
    )

    db_session.add(record)
    db_session.commit()

    response = client.get("session/sessions?limit=5")

    assert response.status_code == 200
    assert len(response.json()) == 1
