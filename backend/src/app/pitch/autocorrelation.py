import numpy as np


def autocorrelation(signal: np.ndarray) -> np.ndarray:
    corr = np.correlate(signal, signal, mode="full")
    return corr[len(corr) // 2 :]


def estimate_frequency(signal: np.ndarray, sample_rate: int) -> float:
    corr = autocorrelation(signal)

    corr[0] = 0

    min_freq = 80
    max_freq = 1000

    min_lag = int(sample_rate / max_freq)
    max_lag = int(sample_rate / min_freq)

    peak_index = np.argmax(corr[min_lag:max_lag]) + min_lag

    return sample_rate / peak_index
