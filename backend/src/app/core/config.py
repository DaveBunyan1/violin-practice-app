from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Infrastructure Settings ---
    DATABASE_URL: str = Field(
        default="sqlite:///./violin_pipeline.db",
        description="The primary database connection string.",
    )

    # --- Audio Ingestion Stream Settings ---
    SAMPLE_RATE: int = Field(
        default=44100, description="Audio capture sampling rate in Hz."
    )
    BUFFER_SIZE: int = Field(
        default=8192, description="Number of audio samples per streaming chunk."
    )
    CHANNELS: int = Field(default=1, description="Number of audio input channels.")
    AMBIENT_NOISE_THRESHOLD: float = Field(
        default=0.0001,
        description="RMS amplitude gate threshold to separate performance signal from background noise.",
    )

    # --- Pitch Detection & Musical Constants ---
    A4_PITCH: float = Field(
        default=440.0,
        description="The standard reference frequency for scientific pitch notation.",
    )

    MAX_RETRIES: int = Field(
        default=3,
        description="Max retry attempts.",
    )

    # Non-configurable mathematical/musical matrices can be immutable tuples
    NOTES: tuple[str, ...] = (
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "Bb",
        "B",
    )

    # Automatically load values from a local .env file if it exists
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Globally instantiated configuration instance
settings = Settings()
