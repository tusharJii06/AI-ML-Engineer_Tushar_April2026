# Release: Smart Checkout v2 (gradual rollout)

## Summary
- New unified checkout API with optimistic UI updates.
- Funnel instrumentation added for `checkout_started` → `payment_success`.

## Known issues (pre-launch)
- Under load, payment provider webhook retries may overlap, causing duplicate success events in edge cases.
- p95 latency may regress briefly while caches warm in new region.

## Rollout
- 10% → 25% → 50% → 100% over 7 days with automated guardrails on error rate and payment failure rate.
