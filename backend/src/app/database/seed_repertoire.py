from app.database.connection import SessionLocal
from app.database.models import RepertoirePiece, RepertoireNote


def seed_data():
    db = SessionLocal()
    try:
        # Check if it's already seeded to prevent duplicates
        exists = (
            db.query(RepertoirePiece)
            .filter(RepertoirePiece.title == "Open Strings Horizon")
            .first()
        )
        if exists:
            print("Database already seeded with initial exercise.")
            return

        # 1. Create the piece container metadata
        piece = RepertoirePiece(
            title="Open Strings Horizon",
            total_duration=5.0,
            bpm=80,
            time_signature_numerator=4,
        )
        db.add(piece)
        db.flush()  # Flushes to get the auto-generated piece.id

        # 2. Add sequential target note windows matching our time model
        notes = [
            RepertoireNote(piece_id=piece.id, note="G3", time=0.0, duration=1.0),
            RepertoireNote(piece_id=piece.id, note="D4", time=1.0, duration=1.0),
            RepertoireNote(piece_id=piece.id, note="A4", time=2.0, duration=1.0),
            RepertoireNote(piece_id=piece.id, note="E5", time=3.0, duration=2.0),
        ]
        db.add_all(notes)
        print(
            "Successfully seeded database with 'Open Strings Horizon' timeline blocks!"
        )

        gym_exists = (
            db.query(RepertoirePiece).filter(RepertoirePiece.title == "Gym").first()
        )

        if not gym_exists:
            bpm = 116
            beat = 60 / bpm

            piece = RepertoirePiece(
                title="Gym",
                total_duration=beat * 17 * 4,
                bpm=bpm,
                time_signature_numerator=4,
            )
            db.add(piece)
            db.flush()

            notes = [
                # Bar 1
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 0, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 1, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 2, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 3, duration=beat
                ),
                # Bar 2
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 4, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 5, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="B4", time=beat * 6, duration=beat
                ),
                # Bar 3
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 8, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 9, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 10, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 11, duration=beat
                ),
                # Bar 4
                RepertoireNote(
                    piece_id=piece.id, note="F#4", time=beat * 12, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="E4", time=beat * 13, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 14, duration=beat
                ),
                # Bar 5
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 16, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 17, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 18, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 19, duration=beat
                ),
                # Bar 6
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 20, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="B4", time=beat * 21, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="C5", time=beat * 22, duration=beat
                ),
                # Bar 7
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 24, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 25, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 26, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 27, duration=beat
                ),
                # Bar 8
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 28, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 29, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 30, duration=beat
                ),
                # Bar 9
                RepertoireNote(
                    piece_id=piece.id, note="B4", time=beat * 32, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D5", time=beat * 33, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 34, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D5", time=beat * 35, duration=beat
                ),
                # Bar 10
                RepertoireNote(
                    piece_id=piece.id, note="E5", time=beat * 36, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 37, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D5", time=beat * 38, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D5", time=beat * 39, duration=beat
                ),
                # Bar 11
                RepertoireNote(
                    piece_id=piece.id, note="B4", time=beat * 40, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D5", time=beat * 41, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 42, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D5", time=beat * 43, duration=beat
                ),
                # Bar 12
                RepertoireNote(
                    piece_id=piece.id, note="E5", time=beat * 44, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="F#5", time=beat * 45, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D5", time=beat * 46, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 47, duration=beat
                ),
                # Bar 13
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 48, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 49, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 50, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D4", time=beat * 51, duration=beat
                ),
                # Bar 14
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 52, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="B4", time=beat * 53, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D5", time=beat * 54, duration=beat
                ),
                # Bar 15
                RepertoireNote(
                    piece_id=piece.id, note="C5", time=beat * 56, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D5", time=beat * 57, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 58, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="D5", time=beat * 59, duration=beat
                ),
                # Bar 16
                RepertoireNote(
                    piece_id=piece.id, note="B4", time=beat * 60, duration=beat
                ),
                RepertoireNote(
                    piece_id=piece.id, note="A4", time=beat * 62, duration=beat
                ),
                # Bar 17
                RepertoireNote(
                    piece_id=piece.id, note="G4", time=beat * 64, duration=beat
                ),
            ]

            db.add_all(notes)

            print("Seeded Gym")

        db.commit()
        print("Seeding complete")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
