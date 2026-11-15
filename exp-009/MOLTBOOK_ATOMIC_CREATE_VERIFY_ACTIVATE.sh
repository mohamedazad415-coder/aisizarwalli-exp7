#!/bin/zsh
set -euo pipefail
cd "$HOME/nft-ai-agent"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
curl -fsSL "https:""//raw.githubusercontent.com/mohamedazad415-coder/aisizarwalli-exp7/main/exp-009/MOLTBOOK_ATOMIC_CREATE_VERIFY_ACTIVATE.py" -o "$TMP"
python3 "$TMP"
