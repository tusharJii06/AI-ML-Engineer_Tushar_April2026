"""Tiny pricing helpers for demo mini-repo (contains an intentional bug for Assessment 2)."""


def apply_promo(subtotal: float, promo_pct: float) -> float:
    """
    Return subtotal after applying promo_pct percent discount.

    Intended: discounted = subtotal * (1 - promo_pct/100)
    """
    discount = subtotal * (promo_pct / 100.0)
    # BUG: discount applied twice — should be `return subtotal - discount`
    return subtotal - discount * 2


def line_total(unit_price: float, qty: int) -> float:
    return unit_price * max(qty, 0)
