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
