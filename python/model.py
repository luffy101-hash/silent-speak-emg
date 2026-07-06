"""1D CNN for multichannel EMG silent-speech classification."""

from __future__ import annotations

import torch
import torch.nn as nn

from config import NUM_CHANNELS, NUM_CLASSES, WINDOW_SAMPLES


class EMGNet(nn.Module):
    """
    Lightweight 1D CNN for 4-channel EMG windows.

    Input:  (batch, channels, time) = (B, 4, 3000)
    Output: (batch, num_classes)
    """

    def __init__(
        self,
        in_channels: int = NUM_CHANNELS,
        num_classes: int = NUM_CLASSES,
        time_steps: int = WINDOW_SAMPLES,
    ):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=7, stride=2, padding=3),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=5, stride=1, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool1d(1),
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = x.squeeze(-1)
        return self.classifier(x)


def save_model(model: EMGNet, path: str) -> None:
    torch.save({"state_dict": model.state_dict()}, path)


def load_model(path: str, device: str = "cpu") -> EMGNet:
    model = EMGNet()
    ckpt = torch.load(path, map_location=device, weights_only=True)
    model.load_state_dict(ckpt["state_dict"])
    model.to(device)
    model.eval()
    return model
