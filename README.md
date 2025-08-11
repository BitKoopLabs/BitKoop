## BitKoop Validator

### Guides
- Mining: [docs/mining.md](docs/mining.md)
- Validating: [docs/validating.md](docs/validating.md)

### How scoring works
- Data window: Only coupons with status VALID created within the last 30 days are considered.
- Per-coupon points by age (relative to `delta_points`, default 7 days):
  - If coupon age < `delta_points`: 100 points
  - If coupon age ≥ `delta_points`: 200 points
- Miner coupon points: Sum of all coupon points attributed to the miner's hotkey.
- Container points: Currently not used (treated as 0); reserved for future infrastructure scoring.
- Combined points per miner: `coupon_weight * coupon_points + container_weight * container_points` (defaults: 0.8 and 0.2).
- Normalization: Let `MAX` be the highest combined points across miners. Each miner's score is `min(1.0, round(points / MAX, 4))`, yielding values in [0, 1].

### Defaults and configurables
- `coupon_weight`: 0.8
- `container_weight`: 0.2
- `delta_points`: 7 days


### Coupon validation lifecycle

- Initial state: On submission (or inbound sync), coupons start as PENDING after base checks (submit window, site exists and active, per-miner/site limits).
- Periodic validation of PENDING: A background task validates PENDING coupons per site using the active validator (Node/Playwright in production, Python fallback otherwise). Success sets status to VALID; failure sets to INVALID. `last_checked_at` is updated.
- Periodic revalidation of VALIDs: Another task rechecks VALID coupons whose `last_checked_at` is older than ~1 day, potentially flipping them to INVALID if they stop working.
- Error/config handling: If a site is missing configuration or is inactive, coupons are deferred and kept PENDING; unexpected validator errors/timeouts mark affected coupons INVALID.
- Manual recheck: MINERS can request recheck of INVALID coupons after a cooldown (`recheck_interval`), which moves them back to PENDING for the next cycle.
- Scheduler: The worker loop in `subnet_validator/tasks/validate_coupons.py` runs periodically (default every minute), executing both the PENDING and stale VALID rechecks.
