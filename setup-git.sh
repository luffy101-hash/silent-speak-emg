#!/usr/bin/env bash
# Install local git hooks for this repo (not pushed to GitHub).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
HOOK_SRC="$ROOT/git-hooks/prepare-commit-msg"
HOOK_DST="$ROOT/.git/hooks/prepare-commit-msg"

if [ ! -d "$ROOT/.git" ]; then
  echo "Error: run this from the repo root after git clone."
  exit 1
fi

if [ ! -f "$HOOK_SRC" ]; then
  echo "Error: missing $HOOK_SRC"
  exit 1
fi

mkdir -p "$ROOT/.git/hooks"
cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

echo "Installed prepare-commit-msg hook."
echo "It removes Co-authored-by: Cursor lines before each commit."
