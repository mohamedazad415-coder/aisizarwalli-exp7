# EXP-007 — Final Report

**Study:** On-chain Details Intent Study  
**Status:** `COMPLETED_TESTED_INCONCLUSIVE`  
**Stopping reason:** `MAXIMUM_DURATION_REACHED`

## Official window

- Start: **2026-10-10T23:51:35.784361+00:00**
- Maximum end: **2026-10-24T23:51:35.784361+00:00**
- Planned stop: **20 distinct `page_view` sessions in each variant OR 14 days, whichever occurred first**

The traffic threshold was not reached, so the study is closed by the maximum-duration rule.

## Final observed results

| Variant | Sessions | engaged_5s | engaged_15s | onchain_clicks | On-chain CTR |
|---|---:|---:|---:|---:|---:|
| CONTROL | 7 | 7 | 2 | 0 | 0% |
| TREATMENT | 4 | 2 | 1 | 0 | 0% |

**Total sessions:** 11  
**Total events:** 23  
**First observed event:** 2026-10-10T23:56:49.954Z  
**Last observed event:** 2026-10-11T20:58:01.306Z

## Integrity check

The event totals reconcile exactly:

- CONTROL: 7 page views + 7 engaged_5s + 2 engaged_15s + 0 onchain_clicks = **16 events**
- TREATMENT: 4 page views + 2 engaged_5s + 1 engaged_15s + 0 onchain_clicks = **7 events**
- Combined: **23 events**, matching the D1 total.

The first observed event occurred after the official launch time, and the last observed event occurred before the official maximum end.

## Primary result

`NO_OBSERVED_ONCHAIN_CLICK_DIFFERENCE`

- CONTROL: **0 / 7 = 0%**
- TREATMENT: **0 / 4 = 0%**

No on-chain-details click was observed in either variant.

## Interpretation

The correct experiment-level classification is:

`TESTED_INCONCLUSIVE`

The study does **not** support a claim that the provenance treatment is better, worse, or equivalent to the control. The sample was small and the planned per-variant traffic threshold was not reached.

Secondary engagement differences are descriptive only and are not treated as statistically reliable evidence.

## Semantic scope

The primary event `onchain_click` measures **intent to inspect on-chain details only**.

It does **not** measure:

- marketplace intent
- an offer
- a sale
- revenue
- profit

## Evidence note

The final counts were obtained from the remote Cloudflare D1 query output at experiment close and independently arithmetic-checked before this archival report was written.
