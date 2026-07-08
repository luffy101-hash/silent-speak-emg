"""Train EMGNet on recorded or synthetic windows."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from config import COMMAND_TO_IDX, COMMANDS, MODEL_DIR, NUM_CHANNELS, RAW_DIR
from model import EMGNet, save_model
from preprocess import bandpass_filter, sliding_windows, synthetic_emg


def load_recordings(data_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load .npy files named {label}_{session}.npy with shape (n_samples, 4)."""
    xs, ys = [], []
    for path in sorted(data_dir.glob("*.npy")):
        label = path.stem.split("_")[0]
        if label not in COMMAND_TO_IDX:
            continue
        raw = np.load(path)
        filtered = bandpass_filter(raw)
        windows = sliding_windows(filtered)
        if len(windows) == 0:
            continue
        xs.append(windows)
        ys.append(np.full(len(windows), COMMAND_TO_IDX[label], dtype=np.int64))
    if not xs:
        return np.empty((0, NUM_CHANNELS, 0)), np.empty(0, dtype=np.int64)
    return np.concatenate(xs, axis=0), np.concatenate(ys, axis=0)


def build_synthetic_dataset(
    reps_per_class: int = 20, seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    """Fallback dataset when no hardware recordings exist yet."""
    xs, ys = [], []
    for idx, _name in enumerate(COMMANDS):
        for rep in range(reps_per_class):
            raw = synthetic_emg(class_idx=idx, seed=seed + idx * 100 + rep)
            filtered = bandpass_filter(raw)
            windows = sliding_windows(filtered)
            if len(windows) == 0:
                continue
            xs.append(windows)
            ys.append(np.full(len(windows), idx, dtype=np.int64))
    return np.concatenate(xs, axis=0), np.concatenate(ys, axis=0)


def train(
    X: np.ndarray,
    y: np.ndarray,
    epochs: int = 50,
    batch_size: int = 16,
    lr: float = 1e-3,
    device: str = "cpu",
) -> EMGNet:
    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.long)
    loader = DataLoader(TensorDataset(X_t, y_t), batch_size=batch_size, shuffle=True)

    model = EMGNet().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    model.train()
    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        correct = 0
        total = 0
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            opt.step()
            total_loss += loss.item() * len(xb)
            correct += (logits.argmax(1) == yb).sum().item()
            total += len(xb)
        acc = correct / max(total, 1)
        print(f"epoch {epoch:03d}  loss={total_loss/total:.4f}  acc={acc:.3f}")

    return model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train SpeakEMG EMGNet")
    parser.add_argument("--data-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--synthetic", action="store_true", help="Use fake EMG data")
    parser.add_argument("--out", type=Path, default=MODEL_DIR / "speahemg.pt")
    args = parser.parse_args()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    if args.synthetic or not any(args.data_dir.glob("*.npy")):
        print("Training on synthetic EMG (no recordings found).")
        X, y = build_synthetic_dataset()
    else:
        print(f"Loading recordings from {args.data_dir}")
        X, y = load_recordings(args.data_dir)

    if len(X) == 0:
        raise SystemExit("No training windows. Record data or use --synthetic.")

    # 80/20 split
    n = len(X)
    idx = np.random.permutation(n)
    split = int(0.8 * n)
    train_idx, val_idx = idx[:split], idx[split:]
    model = train(X[train_idx], y[train_idx], epochs=args.epochs)

    model.eval()
    with torch.no_grad():
        val_x = torch.tensor(X[val_idx], dtype=torch.float32)
        val_y = torch.tensor(y[val_idx], dtype=torch.long)
        pred = model(val_x).argmax(1)
        val_acc = (pred == val_y).float().mean().item()
    print(f"validation accuracy: {val_acc:.3f}")

    save_model(model, str(args.out))
    print(f"saved model -> {args.out}")


if __name__ == "__main__":
    main()
