"""EMG signal preprocessing: bandpass filter, windowing, normalization."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt

from config import (
    BANDPASS_HIGH_HZ,
    BANDPASS_LOW_HZ,
    BANDPASS_ORDER,
    HOP_SAMPLES,
    NUM_CHANNELS,
    SAMPLE_RATE_HZ,
    WINDOW_SAMPLES,
)


def design_bandpass(fs: float = SAMPLE_RATE_HZ) -> tuple[np.ndarray, np.ndarray]:
    """4th-order Butterworth bandpass coefficients (20 to 450 Hz)."""
    nyq = 0.5 * fs
    low = BANDPASS_LOW_HZ / nyq
    high = BANDPASS_HIGH_HZ / nyq
    return butter(BANDPASS_ORDER, [low, high], btype="band")


def bandpass_filter(
    data: np.ndarray, fs: float = SAMPLE_RATE_HZ
) -> np.ndarray:
    """
    Apply zero-phase bandpass to multichannel EMG.

    Args:
        data: shape (n_samples, n_channels) or (n_channels, n_samples)
    """
    if data.ndim != 2:
        raise ValueError("data must be 2D")

    # Work on (n_samples, n_channels)
    if data.shape[0] == NUM_CHANNELS and data.shape[1] != NUM_CHANNELS:
        data = data.T

    b, a = design_bandpass(fs)
    out = np.zeros_like(data, dtype=np.float64)
    for ch in range(data.shape[1]):
        out[:, ch] = filtfilt(b, a, data[:, ch].astype(np.float64))
    return out


def zscore_window(window: np.ndarray) -> np.ndarray:
    """Per-channel zero mean, unit variance for one window."""
    mean = window.mean(axis=0, keepdims=True)
    std = window.std(axis=0, keepdims=True)
    std = np.where(std < 1e-8, 1.0, std)
    return (window - mean) / std


def sliding_windows(
    data: np.ndarray,
    window_samples: int = WINDOW_SAMPLES,
    hop_samples: int = HOP_SAMPLES,
) -> np.ndarray:
    """
    Segment filtered EMG into overlapping windows.

    Args:
        data: (n_samples, n_channels)

    Returns:
        (n_windows, n_channels, window_samples)
    """
    n_samples, n_channels = data.shape
    if n_samples < window_samples:
        return np.empty((0, n_channels, window_samples))

    starts = range(0, n_samples - window_samples + 1, hop_samples)
    windows = []
    for start in starts:
        w = data[start : start + window_samples, :]
        windows.append(zscore_window(w).T)  # (channels, time)
    return np.stack(windows, axis=0)


def parse_csv_line(line: str) -> tuple[int, np.ndarray] | None:
    """Parse firmware CSV line: timestamp_ms,ch0,ch1,ch2,ch3"""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = line.split(",")
    if len(parts) != 5:
        return None
    ts = int(parts[0])
    values = np.array([float(p) for p in parts[1:]], dtype=np.float32)
    return ts, values


def synthetic_emg(
    n_samples: int = 9000,
    n_channels: int = NUM_CHANNELS,
    class_idx: int = 0,
    seed: int | None = None,
) -> np.ndarray:
    """
    Generate fake EMG-like data for pipeline testing without hardware.
    Different classes get slightly different frequency bursts.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(n_samples) / SAMPLE_RATE_HZ
    data = np.zeros((n_samples, n_channels), dtype=np.float64)

    base_freq = 60.0 + class_idx * 12.0
    for ch in range(n_channels):
        burst = np.sin(2 * np.pi * base_freq * t) * np.exp(
            -((t - 1.5 - ch * 0.1) ** 2) / 0.08
        )
        noise = 0.15 * rng.standard_normal(n_samples)
        data[:, ch] = burst + noise

    return data
