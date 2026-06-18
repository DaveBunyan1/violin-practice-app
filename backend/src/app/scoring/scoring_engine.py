from app.models.session_controller import SessionController
from app.scoring.scorer import score_alignment
from app.services.alignment import align_notes


class ScoreEngine:
    def __init__(self, controller: SessionController):
        self.controller = controller
        self.last_score = None

    def compute(self):
        """
        Build a ScoreResult from current session state.
        Pure orchestration layer.
        """

        # 1. Get session
        session = self.controller.get_session()

        # 2. Get data
        expected = self.controller.target.get_expected_sequence()

        # IMPORTANT: decide what you score on
        performed = session.get_performed_notes()

        # 3. Align
        aligned = align_notes(expected, performed)

        # 4. Score
        score = score_alignment(aligned)

        # 5. Optional caching (useful for UI)
        self.last_score = score

        return score
