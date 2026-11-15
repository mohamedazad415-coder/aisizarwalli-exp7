#!/bin/zsh
set -euo pipefail

WRANGLER_VERSION="4.147.0"
DB_NAME="aisizarwalli-exp009"
WORKER_URL="https://aisizarwalli-exp009-collector.aisizarwalli.workers.dev"
ORIGIN="https://mohamedazad415-coder.github.io"
PUBLIC_URL="https://mohamedazad415-coder.github.io/aisizarwalli-exp7/exp-009/public/"
REPO="mohamedazad415-coder/aisizarwalli-exp7"
BRANCH="exp-009-prelaunch"

echo "=== EXP-009 infrastructure preparation ==="
npx wrangler@"$WRANGLER_VERSION" whoami >/dev/null
gh auth status >/dev/null 2>&1
gh auth setup-git >/dev/null 2>&1 || true

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

gh repo clone "$REPO" "$TMP_DIR/repo" -- --quiet
cd "$TMP_DIR/repo"
git fetch -q origin "$BRANCH"
git checkout -q "$BRANCH"
git config user.name "AISIZarwalli Automation"
git config user.email "actions@users.noreply.github.com"

CONFIG="exp-009/public/collector/wrangler.jsonc"
SCHEMA="exp-009/public/collector/schema.sql"

echo "Finding or creating D1..."
LIST_JSON="$(npx wrangler@"$WRANGLER_VERSION" d1 list --json)"
DB_ID="$(python3 - "$DB_NAME" "$LIST_JSON" <<'PY'
import json,sys
name=sys.argv[1]
try: rows=json.loads(sys.argv[2])
except Exception: rows=[]
for r in rows:
    if r.get("name")==name:
        print(r.get("uuid") or r.get("id") or "")
        break
PY
)"

if [[ -z "$DB_ID" ]]; then
  CREATE_OUT="$(npx wrangler@"$WRANGLER_VERSION" d1 create "$DB_NAME" 2>&1)"
  echo "$CREATE_OUT"
  DB_ID="$(printf '%s\n' "$CREATE_OUT" | grep -Eo '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | tail -1)"
fi

if [[ -z "$DB_ID" ]]; then
  echo "ERROR: unable to determine EXP-009 D1 database id."
  exit 1
fi

python3 - "$CONFIG" "$DB_ID" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); dbid=sys.argv[2]
s=p.read_text()
s=s.replace("__EXP009_D1_DATABASE_ID__",dbid)
p.write_text(s)
print("D1 database id configured:",dbid)
PY

if ! git diff --quiet -- "$CONFIG"; then
  git add "$CONFIG"
  git commit -q -m "Configure EXP-009 D1 database"
  git push -q origin "$BRANCH"
fi

echo "Applying D1 schema..."
printf 'y\n' | npx wrangler@"$WRANGLER_VERSION" d1 execute "$DB_NAME"   --remote --file="$SCHEMA" --config="$CONFIG"

echo "Deploying EXP-009 Worker..."
npx wrangler@"$WRANGLER_VERSION" deploy --config="$CONFIG"

echo "Checking PRELAUNCH lifecycle..."
HEALTH="$(curl -fsS "$WORKER_URL/health")"
python3 - "$HEALTH" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d.get("ok") is True
assert d.get("experiment")=="EXP-009"
assert d.get("lifecycle",{}).get("status")=="PRELAUNCH"
print("Worker PRELAUNCH: OK")
PY

echo "Checking CORS..."
HDR="$(mktemp)"
curl -sS -o /dev/null -D "$HDR" -X OPTIONS   -H "Origin: $ORIGIN"   -H "Access-Control-Request-Method: POST"   "$WORKER_URL/event"
grep -qi "access-control-allow-origin: $ORIGIN" "$HDR"
rm -f "$HDR"
echo "CORS: OK"

echo "Confirming PRELAUNCH event rejection..."
RESP_FILE="$(mktemp)"
HTTP_CODE="$(curl -sS -o "$RESP_FILE" -w '%{http_code}' "$WORKER_URL/event"   -H "Origin: $ORIGIN"   -H "Content-Type: application/json"   --data-binary '{"experiment":"EXP-009","source":"moltbook_exp009","variant":"CONTROL","session_id":"exp009-prelaunch-check","event_name":"landing_page_view","client_ts":"2026-11-15T00:00:00Z"}')"
python3 - "$HTTP_CODE" "$RESP_FILE" <<'PY'
import json,sys
code=int(sys.argv[1])
d=json.load(open(sys.argv[2]))
assert code==409, (code,d)
assert d.get("error")=="experiment_not_running"
assert d.get("status")=="PRELAUNCH"
print("PRELAUNCH rejection: OK")
PY
rm -f "$RESP_FILE"

echo "Checking zero baseline..."
STATS="$(curl -fsS "$WORKER_URL/stats")"
python3 - "$STATS" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert d.get("variants",[])==[]
assert int(d.get("totals",{}).get("total_events",0) or 0)==0
print("D1 baseline: ZERO")
PY

echo "Publishing EXP-009 public package..."
git checkout -q main
git pull -q --ff-only origin main
git merge --no-ff "origin/$BRANCH" -m "Publish EXP-009 prelaunch package" >/dev/null
git push -q origin main

echo "Waiting for public page..."
PUBLIC_OK=0
for i in {1..45}; do
  if curl -fsS "$PUBLIC_URL" | grep -q "EXP-009 — Signal Study"; then
    PUBLIC_OK=1
    break
  fi
  sleep 2
done
if [[ "$PUBLIC_OK" -ne 1 ]]; then
  echo "ERROR: EXP-009 public page not reachable."
  exit 1
fi
echo "Public page: OK"

echo "Creating Moltbook distribution post (verification not submitted)..."
python3 "$TMP_DIR/repo/exp-009/MOLTBOOK_STAGE1_POST.py"
