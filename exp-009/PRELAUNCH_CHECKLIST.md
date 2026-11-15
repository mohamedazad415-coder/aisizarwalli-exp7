# EXP-009 Prelaunch Checklist

- [x] EXP-008 timing failure identified and archived.
- [x] One-source / one-destination design chosen.
- [x] Variant assignment occurs after landing.
- [x] Same artwork locked by SHA-256.
- [x] Primary metric defined before launch.
- [x] 50/50 session-scoped assignment.
- [x] No public variant override.
- [x] No cookies or fingerprinting.
- [x] D1 lifecycle control defined.
- [x] PRELAUNCH events rejected.
- [x] Post-deadline events rejected.
- [ ] Create dedicated D1 database aisizarwalli-exp009.
- [ ] Apply schema remotely.
- [ ] Deploy dedicated Worker.
- [ ] Configure D1 database ID.
- [ ] Verify /health, CORS, PRELAUNCH rejection.
- [ ] Publish EXP-009 public path.
- [ ] Verify public page.
- [ ] Confirm zero production baseline.
- [ ] Obtain explicit human approval before Moltbook publication.
- [ ] Publish one Moltbook distribution post.
- [ ] Verify Moltbook challenge exactly once.
- [ ] Activate EXP-009 only after Moltbook publication.
- [ ] Record official launch UTC and maximum end UTC.


## Recovery gate after first challenge expiry

- [x] First verification attempt recorded once; Moltbook returned HTTP 410 (expired).
- [x] Old Stage2 launcher disabled; old Python script guarded.
- [x] Atomic replacement runner added; local model must pass warm-up before any new post.
- [ ] Wait for the post interval and run the atomic launcher once.
- [ ] Confirm new post is verified/bypassed via GET.
- [ ] Confirm Worker changes to RUNNING and record launch UTC.
