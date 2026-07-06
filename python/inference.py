"""Real-time silent-speech inference from serial EMG stream."""

from __future__ import annotations

import argparse
import collections
import time

import numpy as np
import serial
import torch

from config import COMMANDS, MODEL_DIR, NUM_CHANNELS, SAMPLE_RATE_HZ, WINDOW_SAMPLES
from model import load_model
from preprocess import bandpass_filter, parse_csv_line, zscore_window


def run_inference(port: str, model_path: str, baud: int = 115200) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = load_model(model_path, device=device)

    buffer: collections.deque[np.ndarray] = collections.deque(maxlen=WINDOW_SAMPLES * 2)
    raw_rows: list[np.ndarray] = []

    with serial.Serial(port, baud, timeout=1) as ser:
        print("Listening for EMG... (Ctrl+C to stop)")
        last_pred = None
        while True:
            line = ser.readline().decode("utf-8", errors="ignore")
            parsed = parse_csv_line(line)
            if parsed is None:
                continue

            _, values = parsed
            buffer.append(values)
            raw_rows.append(values)
            if len(raw_rows) > WINDOW_SAMPLES * 2:
                raw_rows.pop(0)

            if len(raw_rows) < WINDOW_SAMPLES:
                continue

            window_raw = np.stack(raw_rows[-WINDOW_SAMPLES:], axis=0)
            filtered = bandpass_filter(window_raw)
            w = zscore_window(filtered).T  # (channels, time)

            x = torch.tensor(w, dtype=torch.float32).unsqueeze(0).to(device)
            with torch.no_grad():
                logits = model(x)
                probs = torch.softmax(logits, dim=1)[0]
                idx = int(probs.argmax().item())
                conf = float(probs[idx].item())

            pred = COMMANDS[idx]
            if pred != last_pred or conf > 0.85:
                print(f"{pred}  ({conf:.2f})")
                last_pred = pred


def main() -> None:
    parser = argparse.ArgumentParser(description="Live EMG command inference")
    parser.add_argument("--port", required=True)
    parser.add_argument("--model", default=str(MODEL_DIR / "silentspeak.pt"))
    args = parser.parse_args()

    try:
        run_inference(args.port, args.model)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
