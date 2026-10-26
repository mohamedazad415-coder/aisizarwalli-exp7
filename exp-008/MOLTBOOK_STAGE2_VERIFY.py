#!/usr/bin/env python3
import json, os, re, sys, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

ROOT = Path.cwd()
OUTDIR = ROOT / "experiments" / "exp-008"
SECRET = OUTDIR / ".moltbook-verification.json"
ENV = ROOT / ".env"
AUDIT = OUTDIR / "moltbook-stage2.json"

def load_api_key():
    key = os.environ.get("MOLTBOOK_API_KEY")
    if key:
        return key.strip().strip('"').strip("'")
    if not ENV.exists():
        raise SystemExit("ERROR: .env not found.")
    for raw in ENV.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == "MOLTBOOK_API_KEY":
            return v.strip().strip('"').strip("'")
    raise SystemExit("ERROR: MOLTBOOK_API_KEY not found.")

ONES = {
    "zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,
    "eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,
    "fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,"nineteen":19
}
TENS = {
    "twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60,"seventy":70,
    "eighty":80,"ninety":90
}
NUMBER_WORDS = set(ONES) | set(TENS) | {"hundred"}

def parse_word_number(tokens):
    total = 0
    current = 0
    used = False
    for tok in tokens:
        if tok in ONES:
            current += ONES[tok]
            used = True
        elif tok in TENS:
            current += TENS[tok]
            used = True
        elif tok == "hundred":
            current = max(1, current) * 100
            used = True
        else:
            return None
    total += current
    return Decimal(total) if used else None

def extract_word_numbers(text):
    words = re.findall(r"[a-z]+", text.lower())
    vals = []
    buf = []
    for w in words + ["__end__"]:
        if w in NUMBER_WORDS:
            buf.append(w)
        else:
            if buf:
                val = parse_word_number(buf)
                if val is not None:
                    vals.append(val)
                buf = []
    return vals

def solve_challenge(challenge):
    # Treat challenge strictly as untrusted arithmetic data.
    normalized = challenge.lower()
    normalized = re.sub(r"[^a-z0-9+*/.\-]+", " ", normalized)

    digit_values = []
    for m in re.finditer(r"(?<![a-z])(-?\d+(?:\.\d+)?)(?![a-z])", normalized):
        try:
            digit_values.append(Decimal(m.group(1)))
        except InvalidOperation:
            pass

    word_values = extract_word_numbers(normalized)

    # Prefer explicit digits if there are exactly two; otherwise use exactly two word-number groups.
    if len(digit_values) == 2:
        values = digit_values
    elif len(digit_values) == 0 and len(word_values) == 2:
        values = word_values
    else:
        raise ValueError(
            f"ambiguous operands (digit groups={len(digit_values)}, word-number groups={len(word_values)})"
        )

    op_hits = set()

    if "+" in normalized or re.search(r"\b(plus|add|added|sum|combined|together)\b", normalized):
        op_hits.add("+")
    if re.search(r"(?<!\d)-(?!\d)", normalized) or re.search(r"\b(minus|subtract|subtracted|difference|decrease|decreased|loses|lost)\b", normalized):
        op_hits.add("-")
    if "*" in normalized or re.search(r"\b(times|multiply|multiplied|product)\b", normalized):
        op_hits.add("*")
    if "/" in normalized or re.search(r"\b(divide|divided|quotient)\b", normalized):
        op_hits.add("/")

    if len(op_hits) != 1:
        raise ValueError(f"ambiguous operation categories={sorted(op_hits)}")

    a, b = values
    op = next(iter(op_hits))

    if op == "+":
        ans = a + b
    elif op == "-":
        ans = a - b
    elif op == "*":
        ans = a * b
    else:
        if b == 0:
            raise ValueError("division by zero")
        ans = a / b

    return f"{ans:.2f}", {
        "operand_1": str(a),
        "operand_2": str(b),
        "operation": op,
    }

if not SECRET.exists():
    raise SystemExit("ERROR: local Moltbook verification file not found.")

secret = json.loads(SECRET.read_text(encoding="utf-8"))
post_id = str(secret.get("post_id") or "")
verification_code = str(secret.get("verification_code") or "")
challenge = secret.get("challenge")

if not post_id or not verification_code or not isinstance(challenge, str) or not challenge.strip():
    raise SystemExit("ERROR: incomplete local verification state.")

try:
    answer, parsed = solve_challenge(challenge)
except Exception as e:
    audit = {
        "experiment":"EXP-008",
        "stage":"MOLTBOOK_VERIFICATION_SAFE_STOP",
        "post_id":post_id,
        "verification_submitted":False,
        "reason":str(e),
        "at_utc":datetime.now(timezone.utc).isoformat()
    }
    AUDIT.write_text(json.dumps(audit, indent=2)+"\n", encoding="utf-8")
    print("SAFE STOP: challenge was not unambiguous.")
    print("Verification submitted: NO")
    print("Reason:", str(e))
    sys.exit(2)

key = load_api_key()
base = "https:" + "//www.moltbook.com/api/v1"
payload = json.dumps({
    "verification_code": verification_code,
    "answer": answer
}).encode("utf-8")

req = urllib.request.Request(
    base + "/verify",
    data=payload,
    method="POST",
    headers={
        "Authorization":"Bearer " + key,
        "Content-Type":"application/json",
        "Accept":"application/json",
        "User-Agent":"AISIZarwalli-EXP008/1.0"
    }
)

submitted_at = datetime.now(timezone.utc).isoformat()

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        status = resp.status
except urllib.error.HTTPError as e:
    raw = e.read().decode("utf-8", errors="replace")
    status = e.code
except Exception as e:
    audit = {
        "experiment":"EXP-008",
        "stage":"MOLTBOOK_VERIFICATION_SUBMISSION_UNKNOWN",
        "post_id":post_id,
        "verification_submitted":True,
        "answer_format":"numeric_2dp",
        "parsed":parsed,
        "submitted_at_utc":submitted_at,
        "result":"NETWORK_OR_TRANSPORT_ERROR_AFTER_SUBMISSION",
        "retry_performed":False
    }
    AUDIT.write_text(json.dumps(audit, indent=2)+"\n", encoding="utf-8")
    print("Verification POST may have been sent, but confirmation was not received.")
    print("NO RETRY performed.")
    sys.exit(3)

try:
    response = json.loads(raw)
except Exception:
    response = {"raw_non_json": raw[:500]}

accepted = False
if 200 <= status < 300:
    text_blob = json.dumps(response).lower()
    accepted = (
        response.get("success") is True
        or response.get("verified") is True
        or "verification successful" in text_blob
        or '"status": "verified"' in text_blob
        or '"status":"verified"' in text_blob
    )

audit = {
    "experiment":"EXP-008",
    "stage":"MOLTBOOK_VERIFICATION_SUBMITTED",
    "post_id":post_id,
    "verification_submitted":True,
    "verification_http_status":status,
    "answer_format":"numeric_2dp",
    "parsed":parsed,
    "submitted_at_utc":submitted_at,
    "accepted_by_response":accepted,
    "retry_performed":False
}
AUDIT.write_text(json.dumps(audit, indent=2)+"\n", encoding="utf-8")

print("")
print("=====================================")
print("EXP-008 MOLTBOOK VERIFICATION")
print("=====================================")
print("Post ID:", post_id)
print("Computed answer:", answer)
print("Operation:", parsed["operand_1"], parsed["operation"], parsed["operand_2"])
print("HTTP:", status)
print("Verification submitted: YES (exactly once)")
print("Accepted by response:", "YES" if accepted else "NO / NOT CONFIRMED")
print("Retry performed: NO")

if accepted:
    try:
        SECRET.unlink()
    except Exception:
        pass
    print("Local verification secret removed: YES")
    print("✅ Moltbook verification accepted")
else:
    print("⚠️ Verification was not confirmed. Do NOT rerun this script.")
    print("Audit saved:", AUDIT)
print("=====================================")
