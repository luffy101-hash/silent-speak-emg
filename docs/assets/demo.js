const COMMANDS = [
  "Open", "Close", "Start", "Stop", "Yes",
  "No", "Next", "Back", "Okay", "Cancel",
];

const CHANNEL_COLORS = ["#6ee7b7", "#60a5fa", "#c084fc", "#fb923c"];
const SAMPLE_RATE = 1000;
const BUFFER_LEN = 320;

const canvas = document.getElementById("emg-canvas");
const ctx = canvas.getContext("2d");
const commandGrid = document.getElementById("command-grid");
const resultBlock = document.getElementById("result-block");
const predictionWord = document.getElementById("prediction-word");
const predictionConf = document.getElementById("prediction-conf");
const confidenceFill = document.getElementById("confidence-fill");
const speakBtn = document.getElementById("speak-btn");
const scopeStatus = document.getElementById("scope-status");
const demoHint = document.getElementById("demo-hint");

const buffers = Array.from({ length: 4 }, () => new Float32Array(BUFFER_LEN));
let spikeTarget = 0;
let spikeEnergy = 0;
let selectedCommand = null;
let animating = false;

function initCommands() {
  COMMANDS.forEach((cmd) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "cmd-btn";
    btn.textContent = cmd;
    btn.addEventListener("click", () => runDemo(cmd, btn));
    commandGrid.appendChild(btn);
  });
}

function pushSample(ch, value) {
  const buf = buffers[ch];
  buf.copyWithin(0, 1);
  buf[BUFFER_LEN - 1] = value;
}

function nextSample(ch, t) {
  const base = 2048 + Math.sin(t * 0.02 + ch * 1.7) * 12;
  const noise = (Math.random() - 0.5) * 18;
  const muscle = spikeEnergy * (0.6 + 0.4 * Math.sin(t * 0.08 + ch * 2.1));
  const channelGain = ch === spikeTarget ? 1.4 : 0.55 + ch * 0.1;
  return base + noise + muscle * 180 * channelGain;
}

function drawScope() {
  const w = canvas.width;
  const h = canvas.height;
  const chH = h / 4;

  ctx.fillStyle = "#080a0e";
  ctx.fillRect(0, 0, w, h);

  for (let ch = 0; ch < 4; ch++) {
    const y0 = ch * chH;
    const mid = y0 + chH / 2;

    ctx.strokeStyle = "#1e2430";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, mid);
    ctx.lineTo(w, mid);
    ctx.stroke();

    ctx.strokeStyle = CHANNEL_COLORS[ch];
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    const buf = buffers[ch];
    for (let i = 0; i < BUFFER_LEN; i++) {
      const x = (i / (BUFFER_LEN - 1)) * w;
      const norm = (buf[i] - 2048) / 400;
      const y = mid - norm * (chH * 0.38);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    ctx.fillStyle = CHANNEL_COLORS[ch];
    ctx.font = "10px IBM Plex Mono, monospace";
    ctx.fillText(`ch${ch}`, 6, y0 + 14);
  }
}

let frame = 0;
function tick() {
  frame += 1;
  if (spikeEnergy > 0.01) {
    spikeEnergy *= 0.965;
  } else {
    spikeEnergy = 0;
  }

  for (let ch = 0; ch < 4; ch++) {
    pushSample(ch, nextSample(ch, frame));
  }
  drawScope();
  requestAnimationFrame(tick);
}

function setButtonsDisabled(disabled) {
  commandGrid.querySelectorAll(".cmd-btn").forEach((b) => {
    b.disabled = disabled;
  });
}

function fakeConfidence(correct) {
  const base = 0.62 + Math.random() * 0.28;
  return correct ? Math.min(0.97, base + 0.08) : base * 0.7;
}

async function runDemo(command, btn) {
  if (animating) return;
  animating = true;
  selectedCommand = command;
  setButtonsDisabled(true);
  scopeStatus.textContent = "detecting";
  scopeStatus.classList.add("active");
  demoHint.textContent = "Simulating jaw muscle activation…";

  commandGrid.querySelectorAll(".cmd-btn").forEach((b) => b.classList.remove("selected"));
  btn.classList.add("selected");

  spikeTarget = COMMANDS.indexOf(command) % 4;
  spikeEnergy = 1;

  resultBlock.hidden = false;
  predictionWord.textContent = "…";
  predictionConf.textContent = "—";
  confidenceFill.style.width = "0%";

  await delay(900);

  const conf = fakeConfidence(true);
  const pct = Math.round(conf * 100);
  predictionWord.textContent = command;
  predictionConf.textContent = `${pct}%`;
  confidenceFill.style.width = `${pct}%`;

  scopeStatus.textContent = "classified";
  demoHint.textContent = `Detected "${command}". Hit Speak to hear TTS output.`;
  setButtonsDisabled(false);
  animating = false;
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

speakBtn.addEventListener("click", () => {
  if (!selectedCommand) return;
  const utter = new SpeechSynthesisUtterance(selectedCommand);
  utter.rate = 0.95;
  utter.pitch = 1;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utter);
});

initCommands();
tick();
