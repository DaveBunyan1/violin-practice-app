from app.database.connection import SessionLocal
from app.database.models import RepertoirePiece, RepertoireNote


def seed_data():
    db = SessionLocal()
    try:
        # Check if it's already seeded to prevent duplicates
        exists = (
            db.query(RepertoirePiece)
            .filter(RepertoirePiece.title == "Open Strings")
            .first()
        )
        if exists:
            print("Database already seeded with initial exercise.")
            return

        # 1. Create the piece container metadata
        piece = RepertoirePiece(title="Open Strings Horizon", total_duration=5.0)
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
        db.commit()
        print(
            "Successfully seeded database with 'Open Strings Horizon' timeline blocks!"
        )
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
