from checkoutcalc import apply_promo, line_total


def test_line_total_basic():
    assert line_total(10, 3) == 30


def test_apply_promo_single_application():
    assert apply_promo(100.0, 10.0) == 90.0
