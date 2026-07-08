"""SpeakEMG companion app: command display + TTS."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))

from config import COMMANDS, MODEL_DIR  # noqa: E402

st.set_page_config(page_title="SpeakEMG", page_icon="🎧", layout="centered")

st.title("SpeakEMG")
st.caption("Silent-speech EMG interface")

st.markdown(
    """
    Mouth a command silently. The system classifies your jaw muscle activity
    into one of **10 commands** and speaks it aloud.
    """
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Commands")
    for cmd in COMMANDS:
        st.write(f"• {cmd}")

with col2:
    st.subheader("Status")
    model_path = MODEL_DIR / "speahemg.pt"
    if model_path.exists():
        st.success("Model found")
    else:
        st.warning("Train first: `python python/train.py --synthetic`")

    st.info("Connect ESP32 via USB, then run `python/python/inference.py`")

demo_command = st.selectbox("Demo (manual)", ["none"] + COMMANDS)

if demo_command != "none":
    st.markdown(f"## {demo_command}")
    if st.button("Speak command"):
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.say(demo_command)
            engine.runAndWait()
        except Exception as e:
            st.error(f"TTS failed: {e}")

st.divider()
st.markdown(
    "**Hardware:** 4× Grove EMG · ESP32-S3 · over-ear headphones  \n"
    "**Pipeline:** 1000 Hz -> bandpass 20 to 450 Hz -> 3 s window -> 1D CNN"
)
