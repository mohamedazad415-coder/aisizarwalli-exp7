#!/bin/zsh
set -euo pipefail

WRANGLER_VERSION="4.147.0"
DB_NAME="aisizarwalli-exp008"
WORKER_URL="https://aisizarwalli-exp008-collector.aisizarwalli.workers.dev"
ORIGIN="https://mohamedazad415-coder.github.io"
PUBLIC_URL="https://mohamedazad415-coder.github.io/aisizarwalli-exp7/exp-008/public/"
REPO="mohamedazad415-coder/aisizarwalli-exp7"
BRANCH="exp-008-prelaunch"

echo "=== EXP-008 authenticated deploy ==="
echo "Checking Cloudflare authentication..."
npx wrangler@"$WRANGLER_VERSION" whoami >/dev/null

echo "Checking GitHub authentication..."
gh auth status >/dev/null 2>&1
gh auth setup-git >/dev/null 2>&1 || true

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Cloning deployment package..."
git clone -q "https://github.com/$REPO.git" "$TMP_DIR/repo"
cd "$TMP_DIR/repo"
git fetch -q origin "$BRANCH"
git checkout -q "$BRANCH"

CONFIG="exp-008/public/collector/wrangler.jsonc"
SCHEMA="exp-008/public/collector/schema.sql"

echo "Applying D1 schema..."
npx wrangler@"$WRANGLER_VERSION" d1 execute "$DB_NAME"   --remote   --file="$SCHEMA"   --config="$CONFIG"

echo "Deploying Worker..."
npx wrangler@"$WRANGLER_VERSION" deploy   --config="$CONFIG"

echo "Checking Worker health..."
HEALTH="$(curl -fsS "$WORKER_URL/health")"
python3 - "$HEALTH" <<'PY'
import json, sys
data=json.loads(sys.argv[1])
assert data.get("ok") is True
assert data.get("experiment")=="EXP-008"
assert data.get("storage")=="D1"
assert data.get("deduplication") is True
print("Worker health: OK")
PY

echo "Checking CORS..."
CORS_HEADERS="$(mktemp)"
curl -fsS -o /dev/null -D "$CORS_HEADERS" -X OPTIONS   -H "Origin: $ORIGIN"   -H "Access-Control-Request-Method: POST"   "$WORKER_URL/event"
grep -qi "access-control-allow-origin: $ORIGIN" "$CORS_HEADERS"
rm -f "$CORS_HEADERS"
echo "CORS: OK"

post_event() {
  local variant="$1"
  local session="$2"
  local event="$3"
  curl -fsS "$WORKER_URL/event"     -H "Origin: $ORIGIN"     -H "Content-Type: application/json"     --data-binary "{\"experiment\":\"EXP-008\",\"variant\":\"$variant\",\"session_id\":\"$session\",\"event_name\":\"$event\",\"client_ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >/dev/null
}

CONTROL_TEST="exp008-e2e-control-20261026"
TREATMENT_TEST="exp008-e2e-treatment-20261026"

echo "Running CONTROL telemetry validation..."
for e in page_view engaged_5s engaged_15s acquisition_details_click collector_intent_confirm; do
  post_event CONTROL "$CONTROL_TEST" "$e"
done

echo "Running TREATMENT telemetry validation..."
for e in page_view engaged_5s engaged_15s acquisition_details_click collector_intent_decline; do
  post_event TREATMENT "$TREATMENT_TEST" "$e"
done

echo "Checking aggregate validation..."
STATS="$(curl -fsS "$WORKER_URL/stats")"
python3 - "$STATS" <<'PY'
import json, sys
data=json.loads(sys.argv[1])
rows={r["variant"]:r for r in data.get("variants",[])}
assert rows["CONTROL"]["sessions"]==1
assert rows["CONTROL"]["acquisition_details_clicks"]==1
assert rows["CONTROL"]["collector_intent_confirms"]==1
assert rows["TREATMENT"]["sessions"]==1
assert rows["TREATMENT"]["acquisition_details_clicks"]==1
assert rows["TREATMENT"]["collector_intent_declines"]==1
print("Telemetry validation: OK")
PY

echo "Deleting validation rows..."
npx wrangler@"$WRANGLER_VERSION" d1 execute "$DB_NAME"   --remote   --command="DELETE FROM exp008_events WHERE session_id LIKE 'exp008-e2e-%';"   --config="$CONFIG"

echo "Checking clean pre-public baseline..."
STATS="$(curl -fsS "$WORKER_URL/stats")"
python3 - "$STATS" <<'PY'
import json, sys
data=json.loads(sys.argv[1])
assert data.get("variants",[]) == []
print("Pre-public baseline: ZERO")
PY

echo "Publishing EXP-008 path without changing EXP-007 root..."
git checkout -q main
git pull -q --ff-only origin main
git merge --no-ff "origin/$BRANCH" -m "Publish EXP-008 experiment package" >/dev/null
git push -q origin main

echo "Checking public page..."
PUBLIC_OK=0
for i in {1..30}; do
  if curl -fsS "$PUBLIC_URL" | grep -q "EXP-008 · COLLECTOR INTENT STUDY"; then
    PUBLIC_OK=1
    break
  fi
  sleep 2
done
if [[ "$PUBLIC_OK" -ne 1 ]]; then
  echo "ERROR: public EXP-008 page was not reachable."
  exit 1
fi
echo "Public page: OK"

echo "Removing any pre-launch observations and confirming zero baseline..."
npx wrangler@"$WRANGLER_VERSION" d1 execute "$DB_NAME"   --remote   --command="DELETE FROM exp008_events;"   --config="$CONFIG"

STATS="$(curl -fsS "$WORKER_URL/stats")"
python3 - "$STATS" <<'PY'
import json, sys
data=json.loads(sys.argv[1])
assert data.get("variants",[]) == []
print("Official pre-launch baseline: ZERO")
PY

echo "Recording official launch..."
python3 - <<'PY'
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

root=Path("exp-008")
spec_path=root/"spec.json"
checklist_path=root/"PRELAUNCH_CHECKLIST.md"

start=datetime.now(timezone.utc)
end=start+timedelta(days=14)

launch={
    "experiment":"EXP-008",
    "status":"RUNNING_PUBLIC",
    "launch_utc":start.isoformat(),
    "maximum_end_utc":end.isoformat(),
    "stopping_rule":"20 distinct page_view sessions in EACH variant OR 14 days, whichever occurs first",
    "primary_metric":"collector_intent_confirm_rate_per_page_view_session",
    "public_url":"https://mohamedazad415-coder.github.io/aisizarwalli-exp7/exp-008/public/",
    "worker_url":"https://aisizarwalli-exp008-collector.aisizarwalli.workers.dev",
    "d1_database":"aisizarwalli-exp008",
    "baseline":{
        "control_sessions":0,
        "treatment_sessions":0,
        "total_observed_variants":0,
        "prelaunch_contamination":"NONE_AFTER_RESET"
    },
    "financial_actions_performed":False,
    "blockchain_transactions_performed":False,
    "moltbook_posted":False
}
(root/"launch.json").write_text(json.dumps(launch,indent=2)+"\n",encoding="utf-8")

spec=json.loads(spec_path.read_text(encoding="utf-8"))
spec["status"]="RUNNING_PUBLIC"
spec["official_launch_utc"]=launch["launch_utc"]
spec["maximum_end_utc"]=launch["maximum_end_utc"]
spec["public_url"]=launch["public_url"]
spec_path.write_text(json.dumps(spec,indent=2)+"\n",encoding="utf-8")

c=checklist_path.read_text(encoding="utf-8")
for old,new in [
("- [ ] Apply schema.sql remotely.","- [x] Apply schema.sql remotely."),
("- [ ] Deploy dedicated Worker.","- [x] Deploy dedicated Worker."),
("- [ ] Publish from dedicated EXP-008 public location.","- [x] Publish from dedicated EXP-008 public location."),
("- [ ] Verify /health and CORS.","- [x] Verify /health and CORS."),
("- [ ] Run CONTROL telemetry chain.","- [x] Run CONTROL telemetry chain."),
("- [ ] Run TREATMENT telemetry chain.","- [x] Run TREATMENT telemetry chain."),
("- [ ] Delete validation rows.","- [x] Delete validation rows."),
("- [ ] Confirm public D1 baseline = 0.","- [x] Confirm public D1 baseline = 0."),
("- [ ] Record official launch UTC and maximum end UTC.","- [x] Record official launch UTC and maximum end UTC.")
]:
    c=c.replace(old,new)
checklist_path.write_text(c,encoding="utf-8")

print("Launch UTC:",launch["launch_utc"])
print("Maximum end UTC:",launch["maximum_end_utc"])
PY

git add exp-008/launch.json exp-008/spec.json exp-008/PRELAUNCH_CHECKLIST.md
git commit -q -m "Record EXP-008 official launch"
git push -q origin main

echo ""
echo "====================================="
echo "✅ EXP-008 RUNNING PUBLIC"
echo "====================================="
echo "Public URL: $PUBLIC_URL"
echo "Worker: $WORKER_URL"
echo "D1 baseline: ZERO"
echo "Financial actions: NONE"
echo "Blockchain transactions: NONE"
echo "Moltbook post: NOT PUBLISHED"
echo "====================================="
