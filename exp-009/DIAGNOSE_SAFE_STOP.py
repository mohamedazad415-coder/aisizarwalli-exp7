#!/usr/bin/env python3
"""Read-only EXP-009 SAFE STOP diagnostic. Never submits or retries verification."""
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path.home() / "nft-ai-agent"
EXP_DIR = ROOT / "experiments" / "exp-009"
ATTEMPT_FILE = EXP_DIR / "moltbook-stage2-attempt.json"
LAUNCH_FILE = EXP_DIR / "launch.json"
ENV_FILE = ROOT / ".env"
POST_ID = "cb13c43f-0bd4-4f98-82d6-b8ad13da7364"
MOLTBOOK_POST_URL = "https://www.moltbook.com/api/v1/posts/" + POST_ID
WORKER = "https://aisizarwalli-exp009-collector.aisizarwalli.workers.dev"

SENSITIVE = ("verification_code", "api_key", "authorization", "token", "secret",
             "password", "challenge_text", "challenge")

def scrub(value):
    if isinstance(value, dict):
        return {
            k: scrub(v) for k, v in value.items()
            if not any(s in k.lower() for s in SENSITIVE)
        }
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value

def show_json(label, value):
    print("\n" + label)
    print(json.dumps(scrub(value), ensure_ascii=False, indent=2))

def read_api_key():
    value = os.environ.get("MOLTBOOK_API_KEY")
    if value:
        return value.strip().strip('"').strip("'")
    if not ENV_FILE.exists():
        return None
    for raw in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            if key.strip() == "MOLTBOOK_API_KEY":
                return val.strip().strip('"').strip("'")
    return None

def get_json(url, headers=None):
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "AISIZarwalli-EXP009-Diagnostic/1.0",
                      **(headers or {})}, method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                return response.status, json.loads(raw)
            except Exception:
                return response.status, {"raw_response": raw[:2000]}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except Exception:
            body = {"raw_response": raw[:2000]}
        return error.code, body
    except Exception as error:
        return None, {"network_error_type": type(error).__name__, "message": str(error)[:300]}

print("EXP-009 — DIAGNOSTIC EN LECTURE SEULE")
print("Aucun POST, aucune nouvelle vérification, aucune modification de fichier.")
print("")

if ATTEMPT_FILE.exists():
    try:
        attempt = json.loads(ATTEMPT_FILE.read_text(encoding="utf-8"))
        keys = ("post_id", "status", "http_status", "response_message",
                "error_type", "attempted_at_utc", "submission_count")
        show_json("1) Marqueur de tentative local", {k: attempt.get(k) for k in keys})
    except Exception as error:
        print("1) Marqueur local illisible:", type(error).__name__)
else:
    print("1) Marqueur local: absent")

if LAUNCH_FILE.exists():
    try:
        launch = json.loads(LAUNCH_FILE.read_text(encoding="utf-8"))
        keys = ("status", "moltbook_verification", "launch_utc", "maximum_end_utc")
        show_json("2) Fichier de lancement local", {k: launch.get(k) for k in keys})
    except Exception as error:
        print("2) Fichier de lancement illisible:", type(error).__name__)
else:
    print("2) Fichier de lancement: absent")

key = read_api_key()
if key:
    code, post = get_json(MOLTBOOK_POST_URL, {"Authorization": "Bearer " + key})
    show_json("3) État du post Moltbook (GET uniquement) — HTTP " + str(code), post)
else:
    print("3) Post Moltbook: clé absente du .env; vérification GET ignorée (aucune clé affichée).")

for label, endpoint in (("4) Worker /health", "/health"), ("5) Worker /stats", "/stats")):
    code, data = get_json(WORKER + endpoint)
    show_json(label + " — HTTP " + str(code), data)

print("\nFIN DU DIAGNOSTIC. Ne relancez pas le script de vérification EXP-009.")
