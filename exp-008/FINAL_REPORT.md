# EXP-008 Final Report

## Status
**COMPLETED_NO_DATA**

## Stop condition
Maximum duration reached.

- Official launch: 2026-10-26T21:09:01.523588+00:00
- Maximum end: 2026-11-09T21:09:01.523588+00:00
- Final CONTROL page-view sessions: **0**
- Final TREATMENT page-view sessions: **0**
- Total D1 events: **0**
- First production event: **none**
- Last production event: **none**

## Primary metric
`collector_intent_confirm_rate_per_page_view_session`

The metric is **not evaluable** because neither variant received a recorded page-view session.

## Result
**TEST_NOT_EVALUABLE**

Classification:
- NO_PRODUCTION_EVENTS_OBSERVED
- NO_MEASURABLE_EXPOSURE
- MAXIMUM_DURATION_REACHED
- TEST_NOT_EVALUABLE
- COMPLETED_NO_DATA

## Interpretation
No production telemetry was recorded after the official launch baseline reset. Therefore EXP-008 provides no evidence for or against the hypothesis that showing the proposed collector price before acquisition details changes collector intent.

The prelaunch telemetry chain for both CONTROL and TREATMENT had been validated before the baseline reset. Still, a zero-event production result cannot distinguish, by itself, between zero real visitors and a post-launch availability/delivery problem.

## Claims we must not make
- CONTROL performed better.
- TREATMENT performed better.
- The variants are equivalent.
- Visitors accepted or rejected the 0.01 ETH proposal.

## Next experiment
EXP-009 should move one step earlier in the funnel and test **traffic/distribution acquisition** before running another pricing or collector-intent experiment.
