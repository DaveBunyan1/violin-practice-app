from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Define the local database file path
DATABASE_URL = "sqlite:///./violin_pipeline.db"

# Create the core SQLAlchemy engine.
# 'connect_args' is required only for SQLite to allow multi-threaded access.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a SessionLocal class. Each instance of this class will be a
# distinct database transaction session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The base class our database models will inherit from to register with the ORM
Base = declarative_base()


def get_db():
    """
    FastAPI dependency provider. Yields a database session to an endpoint
    context and automatically closes it when the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
