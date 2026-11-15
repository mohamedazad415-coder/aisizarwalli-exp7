#!/usr/bin/env python3
import json, os, re, sys, subprocess, urllib.request, urllib.error, tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone

ROOT = Path.home() / "nft-ai-agent"
EXP_DIR = ROOT / "experiments" / "exp-009"
SECRET_FILE = EXP_DIR / ".moltbook-verification.json"
ATTEMPT_FILE = EXP_DIR / "moltbook-stage2-attempt.json"
LAUNCH_FILE = EXP_DIR / "launch.json"
FINAL_FILE = EXP_DIR / "moltbook-stage2.json"
ENV_FILE = ROOT / ".env"

EXPECTED_POST_ID = "cb13c43f-0bd4-4f98-82d6-b8ad13da7364"
ANSWER = "19.00"
DB_NAME = "aisizarwalli-exp009"
WORKER = "https://aisizarwalli-exp009-collector.aisizarwalli.workers.dev"
WRANGLER_VERSION = "4.147.0"

def stop(message, code=1):
    print("SAFE STOP:", message)
    sys.exit(code)

def read_api_key():
    value = os.environ.get("MOLTBOOK_API_KEY")
    if value:
        return value.strip().strip('"').strip("'")
    if not ENV_FILE.exists():
        stop(".env introuvable.")
    for raw in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        if key.strip() == "MOLTBOOK_API_KEY":
            return val.strip().strip('"').strip("'")
    stop("MOLTBOOK_API_KEY introuvable dans .env.")

def get_json(url):
    req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"AISIZarwalli-EXP009/1.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def check_prelaunch():
    health = get_json(WORKER + "/health")
    if health.get("ok") is not True or health.get("experiment") != "EXP-009":
        stop("Worker EXP-009 indisponible ou inattendu.")
    lifecycle = health.get("lifecycle") or {}
    if lifecycle.get("status") not in ("PRELAUNCH", "RUNNING"):
        stop("Etat Worker inattendu: " + str(lifecycle.get("status")))
    stats = get_json(WORKER + "/stats")
    total = int((stats.get("totals") or {}).get("total_events") or 0)
    if total != 0 and lifecycle.get("status") == "PRELAUNCH":
        stop("La baseline D1 n'est pas nulle; aucune activation automatique.")
    return health, stats

def deploy_latest_worker():
    print("Mise à jour du Worker avec les règles d'arrêt complètes...")
    base = "https:" + "//raw.githubusercontent.com/mohamedazad415-coder/aisizarwalli-exp7/main/exp-009/public/collector/"
    with tempfile.TemporaryDirectory(prefix="exp009-deploy-") as temp:
        root = Path(temp)
        (root / "src").mkdir(parents=True, exist_ok=True)
        for remote, local in [
            ("schema.sql", root / "schema.sql"),
            ("wrangler.jsonc", root / "wrangler.jsonc"),
            ("src/index.js", root / "src" / "index.js")
        ]:
            with urllib.request.urlopen(base + remote, timeout=30) as response:
                local.write_bytes(response.read())

        schema_cmd = [
            "npx", "wrangler@" + WRANGLER_VERSION, "d1", "execute",
            DB_NAME, "--remote", "--file=" + str(root / "schema.sql")
        ]
        applied = subprocess.run(
            schema_cmd, cwd=str(ROOT), input="y\n", text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if applied.returncode != 0:
            print(applied.stdout[-1800:])
            stop("Impossible de mettre à jour le schéma D1 avant la vérification.")

        deployed = subprocess.run(
            ["npx", "wrangler@" + WRANGLER_VERSION, "deploy", "--config=" + str(root / "wrangler.jsonc")],
            cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        if deployed.returncode != 0:
            print(deployed.stdout[-1800:])
            stop("Le Worker n'a pas pu être déployé; aucun challenge soumis.")

def wrangler_update(launch_utc, end_utc):
    sql = (
        "UPDATE exp009_control "
        "SET status='RUNNING', "
        "launch_utc='" + launch_utc + "', "
        "maximum_end_utc='" + end_utc + "', "
        "updated_at='" + launch_utc + "' "
        "WHERE experiment='EXP-009' "
        "AND status='PRELAUNCH' "
        "AND launch_utc IS NULL "
        "AND maximum_end_utc IS NULL;"
    )
    command = ["npx", "wrangler@" + WRANGLER_VERSION, "d1", "execute", DB_NAME, "--remote", "--command=" + sql]
    print("Activation du contrôle D1...")
    result = subprocess.run(
        command, cwd=str(ROOT), input="y\n", text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if result.returncode != 0:
        print(result.stdout[-1800:])
        stop("La vérification Moltbook est acceptée, mais l'activation D1 doit être reprise. Ne soumettez PAS le challenge à nouveau.")

def main():
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    deploy_latest_worker()

    attempt = None
    if ATTEMPT_FILE.exists():
        try:
            attempt = json.loads(ATTEMPT_FILE.read_text())
        except Exception:
            stop("Fichier d'état de soumission illisible; aucun nouvel envoi.")
        if attempt.get("post_id") != EXPECTED_POST_ID:
            stop("Post ID différent; aucun envoi.")
        if attempt.get("status") not in ("VERIFIED", "VERIFIED_PENDING_ACTIVATION"):
            stop("Une tentative de vérification existe déjà. Aucun nouvel envoi ne sera effectué.")
    else:
        if not SECRET_FILE.exists():
            stop("Secret local absent; aucun envoi.")
        secret = json.loads(SECRET_FILE.read_text(encoding="utf-8"))
        post_id = str(secret.get("post_id", ""))
        verification_code = str(secret.get("verification_code", ""))
        challenge = str(secret.get("challenge", ""))
        if post_id != EXPECTED_POST_ID:
            stop("Post ID inattendu; aucun envoi.")
        if not verification_code:
            stop("Code de vérification absent; aucun envoi.")
        normalized = re.sub(r"[^a-z0-9]+", " ", challenge.lower())
        if not (re.search(r"twenty\s+six", normalized) and "reduce" in normalized and "seven" in normalized):
            stop("Le texte du challenge ne correspond pas au calcul validé; aucun envoi.")

        api_key = read_api_key()
        if not api_key:
            stop("MOLTBOOK_API_KEY vide; aucun envoi.")

        health, stats = check_prelaunch()
        if (health.get("lifecycle") or {}).get("status") != "PRELAUNCH":
            stop("Le Worker n'est pas en PRELAUNCH; aucun challenge soumis.")
        if int((stats.get("totals") or {}).get("total_events") or 0) != 0:
            stop("La baseline n'est pas à zéro; aucun challenge soumis.")

        auth_check = subprocess.run(
            ["npx", "wrangler@" + WRANGLER_VERSION, "whoami"],
            cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        if auth_check.returncode != 0:
            print(auth_check.stdout[-1200:])
            stop("Authentification Cloudflare indisponible; aucun challenge soumis.")

        # Persist an irreversible-attempt marker BEFORE the one and only POST.
        attempt = {
            "experiment":"EXP-009",
            "post_id":EXPECTED_POST_ID,
            "status":"SUBMISSION_ATTEMPTED",
            "answer":ANSWER,
            "attempted_at_utc":datetime.now(timezone.utc).isoformat(),
            "submission_count":1
        }
        ATTEMPT_FILE.write_text(json.dumps(attempt, indent=2)+"\n", encoding="utf-8")
        os.chmod(ATTEMPT_FILE, 0o600)

        payload = json.dumps({
            "verification_code":verification_code,
            "answer":ANSWER
        }).encode("utf-8")
        request = urllib.request.Request(
            "https:" + "//www.moltbook.com/api/v1/verify",
            data=payload,
            method="POST",
            headers={
                "Authorization":"Bearer " + api_key,
                "Content-Type":"application/json",
                "Accept":"application/json",
                "User-Agent":"AISIZarwalli-EXP009/1.0"
            }
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                http_status = response.status
                response_body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            http_status = error.code
            response_body = error.read().decode("utf-8", errors="replace")
        except Exception as error:
            attempt["http_status"] = None
            attempt["status"] = "SUBMISSION_OUTCOME_UNKNOWN"
            attempt["error_type"] = type(error).__name__
            ATTEMPT_FILE.write_text(json.dumps(attempt, indent=2)+"\n", encoding="utf-8")
            stop("Résultat réseau incertain. Ne relancez pas la vérification; contrôlez le statut du post manuellement.")

        try:
            response_json = json.loads(response_body)
        except Exception:
            response_json = {}

        if not (200 <= http_status < 300 and response_json.get("success") is True):
            attempt["http_status"] = http_status
            attempt["status"] = "VERIFICATION_NOT_CONFIRMED"
            attempt["response_message"] = str(response_json.get("message") or response_json.get("error") or "No success confirmation")
            ATTEMPT_FILE.write_text(json.dumps(attempt, indent=2)+"\n", encoding="utf-8")
            stop("Moltbook n'a pas confirmé la vérification. Aucun retry automatique.")
        
        attempt["http_status"] = http_status
        attempt["status"] = "VERIFIED"
        attempt["verified_at_utc"] = datetime.now(timezone.utc).isoformat()
        attempt["response_message"] = str(response_json.get("message") or "Verification successful")
        ATTEMPT_FILE.write_text(json.dumps(attempt, indent=2)+"\n", encoding="utf-8")
        SECRET_FILE.unlink(missing_ok=True)
        print("Moltbook: VERIFIED (HTTP " + str(http_status) + ")")
        print("Secret local de vérification supprimé.")

    # If verification was already confirmed in a prior run, do not POST again.
    if LAUNCH_FILE.exists():
        launch = json.loads(LAUNCH_FILE.read_text(encoding="utf-8"))
        if launch.get("status") == "RUNNING":
            print("EXP-009 est déjà RUNNING.")
            print("Launch UTC:", launch.get("launch_utc"))
            print("Maximum end UTC:", launch.get("maximum_end_utc"))
            return
        if launch.get("status") != "VERIFIED_PENDING_ACTIVATION":
            stop("Fichier launch.json dans un état inattendu.")
    else:
        launch_time = datetime.now(timezone.utc).replace(microsecond=0)
        end_time = launch_time + timedelta(days=7)
        launch = {
            "experiment":"EXP-009",
            "status":"VERIFIED_PENDING_ACTIVATION",
            "post_id":EXPECTED_POST_ID,
            "moltbook_verification":"ACCEPTED",
            "moltbook_http_status":attempt.get("http_status"),
            "moltbook_answer":ANSWER,
            "launch_utc":launch_time.isoformat().replace("+00:00","Z"),
            "maximum_end_utc":end_time.isoformat().replace("+00:00","Z"),
            "maximum_duration_days":7,
            "activation_rule":"Official clock starts only after Moltbook verification is accepted."
        }
        LAUNCH_FILE.write_text(json.dumps(launch, indent=2)+"\n", encoding="utf-8")

    launch_utc = launch["launch_utc"]
    end_utc = launch["maximum_end_utc"]

    health, stats = check_prelaunch()
    state = (health.get("lifecycle") or {}).get("status")
    if state == "PRELAUNCH":
        wrangler_update(launch_utc, end_utc)
    elif state != "RUNNING":
        stop("Etat Worker inattendu avant activation: " + str(state))

    final_health = get_json(WORKER + "/health")
    final_state = final_health.get("lifecycle") or {}
    if final_state.get("status") != "RUNNING":
        stop("La vérification Moltbook est faite, mais Worker/D1 n'a pas confirmé RUNNING. Ne soumettez pas le challenge à nouveau.")
    if final_state.get("launch_utc") != launch_utc or final_state.get("maximum_end_utc") != end_utc:
        stop("Les dates du Worker ne correspondent pas à l'audit local.")

    launch["status"] = "RUNNING"
    launch["activated_at_utc"] = datetime.now(timezone.utc).isoformat()
    LAUNCH_FILE.write_text(json.dumps(launch, indent=2)+"\n", encoding="utf-8")

    final = {
        "experiment":"EXP-009",
        "post_id":EXPECTED_POST_ID,
        "moltbook_verification":"ACCEPTED",
        "verification_submitted_once":True,
        "answer":ANSWER,
        "http_status":attempt.get("http_status"),
        "launch_utc":launch_utc,
        "maximum_end_utc":end_utc,
        "worker_status":final_state.get("status"),
        "d1_baseline_events":0,
        "financial_actions":"NONE",
        "blockchain_transactions":"NONE"
    }
    FINAL_FILE.write_text(json.dumps(final, indent=2)+"\n", encoding="utf-8")

    print("")
    print("=====================================")
    print("✅ EXP-009 RUNNING PUBLIC")
    print("=====================================")
    print("Post ID:", EXPECTED_POST_ID)
    print("Moltbook verification: ACCEPTED")
    print("Verification submitted: exactly once")
    print("Launch UTC:", launch_utc)
    print("Maximum end UTC:", end_utc)
    print("Worker status:", final_state.get("status"))
    print("D1 baseline events: 0")
    print("Financial actions: NONE")
    print("Blockchain transactions: NONE")
    print("=====================================")

if __name__ == "__main__":
    main()
