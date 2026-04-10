# Bug: Checkout promo math wrong for 10% off

## Expected behavior
When applying a 10% promotion to a $100 subtotal, the customer should pay **$90**.

## Actual behavior
Customers report paying **$80** for the same scenario (discount looks doubled).

## Environment
- Python 3.11
- Service: `checkoutcalc` library inside `mini_repo`
- OS: Linux (prod containers)

## Reproduction hints
- Call pricing helper used by checkout API: `apply_promo(100.0, 10.0)`
- Fails in unit test `test_apply_promo_single_application`
- Deploy version: `2026.04.05-14`

## Customer impact
Medium-high: incorrect totals at checkout; finance escalation.
