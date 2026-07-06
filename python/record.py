"""Record labeled EMG windows from serial stream."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import serial

from config import COMMAND_TO_IDX, RAW_DIR, SAMPLE_RATE_HZ, WINDOW_SAMPLES
from preprocess import bandpass_filter, parse_csv_line


def record_session(
    port: str,
    label: str,
    duration_sec: float = 5.0,
    baud: int = 115200,
) -> np.ndarray:
    if label not in COMMAND_TO_IDX:
        raise ValueError(f"Unknown label. Choose from: {list(COMMAND_TO_IDX)}")

    samples = []
    with serial.Serial(port, baud, timeout=1) as ser:
        print(f"Recording '{label}' for {duration_sec}s. Mouth the word silently...")
        deadline = time.time() + duration_sec
        while time.time() < deadline:
            line = ser.readline().decode("utf-8", errors="ignore")
            parsed = parse_csv_line(line)
            if parsed is None:
                continue
            _, values = parsed
            samples.append(values)

    if len(samples) < WINDOW_SAMPLES:
        raise RuntimeError(
            f"Only got {len(samples)} samples; need at least {WINDOW_SAMPLES}. "
            "Check serial port and firmware."
        )

    raw = np.stack(samples, axis=0)
    return bandpass_filter(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="Record EMG for one command label")
    parser.add_argument("--port", required=True, help="Serial port, e.g. /dev/cu.usbmodem101")
    parser.add_argument("--label", required=True, help="One of the 10 commands, e.g. Open")
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--out-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    data = record_session(args.port, args.label, args.duration)
    ts = int(time.time())
    out_path = args.out_dir / f"{args.label}_{ts}.npy"
    np.save(out_path, data)
    print(f"saved {data.shape} -> {out_path}")


if __name__ == "__main__":
    main()
