"""
Auto-generated minimal repro (Assessment 2).
Run from repo root: python -m pytest D:/Offcampus/purple/assessment2_bug_triage/artifacts/repro/test_repro_checkout.py -q
"""
import sys
from pathlib import Path

_MINI = Path(__file__).resolve().parents[2] / "mini_repo"
sys.path.insert(0, str(_MINI))

from checkoutcalc import apply_promo


def test_repro_promo_should_be_single_discount():
    assert apply_promo(100.0, 10.0) == 90.0
