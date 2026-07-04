import numpy as np


class SineWaveGenerator:

    def __init__(
        self,
        sample_rate: int,
        block_size: int,
        frequency: float,
        amplitude: float = 0.5,
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.frequency = frequency
        self.amplitude = amplitude
        self.phase = 0.0

    def next_chunk(self) -> np.ndarray:

        t = (np.arange(self.block_size) + self.phase) / self.sample_rate

        samples = self.amplitude * np.sin(2 * np.pi * self.frequency * t)

        self.phase += self.block_size

        return samples.astype(np.float32).reshape(-1, 1)
