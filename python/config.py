"""Shared constants for SilentSpeak pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MODEL_DIR = DATA_DIR / "models"

SAMPLE_RATE_HZ = 1000
WINDOW_SEC = 3.0
WINDOW_SAMPLES = int(SAMPLE_RATE_HZ * WINDOW_SEC)
HOP_SAMPLES = WINDOW_SAMPLES // 2  # 50% overlap

NUM_CHANNELS = 4
BANDPASS_LOW_HZ = 20.0
BANDPASS_HIGH_HZ = 450.0
BANDPASS_ORDER = 4

COMMANDS = [
    "Open",
    "Close",
    "Start",
    "Stop",
    "Yes",
    "No",
    "Next",
    "Back",
    "Okay",
    "Cancel",
]

NUM_CLASSES = len(COMMANDS)
COMMAND_TO_IDX = {name: i for i, name in enumerate(COMMANDS)}
