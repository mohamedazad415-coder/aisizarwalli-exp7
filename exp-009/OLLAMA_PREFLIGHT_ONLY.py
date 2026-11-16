#!/usr/bin/env python3
"""EXP-009: Ollama-only preflight. No Moltbook API calls, posts or activation."""
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent
path = BASE / "MOLTBOOK_ATOMIC_CREATE_VERIFY_ACTIVATE.py"
spec = importlib.util.spec_from_file_location("exp009_atomic_preflight", path)
atomic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atomic)

def main():
    print("EXP-009 contrôle local Ollama uniquement : aucune publication ni activation.")
    env = atomic.read_env_values()
    model = atomic.check_ollama(env)
    print("PRÉTEST OLLAMA VALIDÉ :", model)
    print("EXP-009 : aucune action Moltbook effectuée.")

if __name__ == "__main__":
    main()
