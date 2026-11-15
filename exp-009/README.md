# EXP-009 — Distribution Activation → Artwork Open

EXP-009 fixes the operational failure mode exposed by EXP-008.

## Core design
One Moltbook distribution post points to one landing URL. Visitors are randomized 50/50 **after** they arrive, so CONTROL and TREATMENT do not depend on two different feed exposures.

### CONTROL
- EXPERIMENTAL ARTWORK
- Deterministic Signal Trace
- A static generative signal study.

### TREATMENT
- CAN YOU READ THE SIGNAL?
- What do you see in this trace?
- Open the full work before reading the explanation.

Common CTA: **Open full artwork**

## Operational gate
At least one production landing session must be recorded within 24 hours after Moltbook publication and activation. If not, diagnose distribution/delivery before interpreting content.

## Primary metric
Artwork opens / distinct landing-page sessions.

## Stop rule
12 landing sessions in each arm OR 7 days, whichever comes first.

If fewer than 10 total sessions are observed, any A/B result is low-exposure and not evaluable.

## Safety
No wallet connection, payment, listing, purchase, blockchain transaction, cookies, fingerprinting, IP storage, UA storage, or referrer storage.


## Recovery after the expired Moltbook challenge

The first distribution post (ID `cb13c43f-0bd4-4f98-82d6-b8ad13da7364`) remains pending because its one verification attempt returned HTTP 410. Its code must never be reused.

Use only `MOLTBOOK_ATOMIC_CREATE_VERIFY_ACTIVATE.sh` for the next attempt. The older `MOLTBOOK_STAGE2_VERIFY_AND_ACTIVATE.sh` launcher is deprecated and disabled.

The atomic runner:
- checks the old post and the 31-minute post interval before publishing;
- confirms the Worker is PRELAUNCH with a zero-event baseline;
- confirms a local Ollama model is available and passes a warm-up arithmetic test **before** creating a new public post;
- asks for the literal confirmation `POST`;
- creates one new post, solves the received arithmetic challenge twice locally, and submits at most one `/verify` request;
- never retries an uncertain or failed post/verification request;
- starts the seven-day clock only after Moltbook confirms the post as verified/bypassed and the Worker confirms RUNNING.

If Ollama is unavailable, the model outputs disagree, the challenge is ambiguous, or any network result is uncertain, the runner stops without guessing. The API key and verification code remain local and are never printed. No wallet, payment, marketplace, or blockchain action is performed.

Run from Terminal:

```bash
cd "$HOME/nft-ai-agent"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
curl -fsSL "https:""//raw.githubusercontent.com/mohamedazad415-coder/aisizarwalli-exp7/main/exp-009/MOLTBOOK_ATOMIC_CREATE_VERIFY_ACTIVATE.sh" -o "$TMP"
zsh "$TMP"
```
