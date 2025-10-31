"""Tests for ludolog.playtime."""
from ludolog.playtime import Playtime, combine_playtimes, parse_playtime, playtime_overlap


def test_default_label_unknown():
    assert Playtime().label() == "unknown"


def test_equal_minutes_label():
    pt = Playtime(min_minutes=45, max_minutes=45)
    assert pt.label() == "45 min"


def test_range_label():
    pt = Playtime(min_minutes=30, max_minutes=60)
    assert pt.label() == "30-60 min"


def test_max_only_label():
    pt = Playtime(max_minutes=90)
    assert pt.label() == "≤90 min"


def test_min_only_label():
    pt = Playtime(min_minutes=30)
    assert pt.label() == "≥30 min"


def test_fits_within_range():
    pt = Playtime(min_minutes=30, max_minutes=60)
    assert pt.fits(45) is True
    assert pt.fits(20) is False
    assert pt.fits(70) is False


def test_fits_with_slack():
    pt = Playtime(min_minutes=30, max_minutes=60)
    assert pt.fits(65, slack=10) is True


def test_fits_no_limits():
    assert Playtime().fits(999) is True


def test_midpoint():
    pt = Playtime(min_minutes=20, max_minutes=40)
    assert pt.midpoint() == 30


def test_midpoint_single_value():
    pt = Playtime(max_minutes=60)
    assert pt.midpoint() == 60


def test_to_dict_roundtrip():
    pt = Playtime(min_minutes=10, max_minutes=20)
    restored = Playtime.from_dict(pt.to_dict())
    assert restored.min_minutes == 10
    assert restored.max_minutes == 20


def test_parse_dash_range():
    pt = parse_playtime("30-60 min")
    assert pt.min_minutes == 30
    assert pt.max_minutes == 60


def test_parse_single_value():
    pt = parse_playtime("45 minutes")
    assert pt.min_minutes == 45
    assert pt.max_minutes == 45


def test_parse_empty():
    pt = parse_playtime("")
    assert pt.min_minutes is None


def test_parse_invalid():
    pt = parse_playtime("no digits here")
    assert pt.min_minutes is None


def test_combine_playtimes():
    a = Playtime(min_minutes=30, max_minutes=60)
    b = Playtime(min_minutes=20, max_minutes=90)
    combined = combine_playtimes(a, b)
    assert combined.min_minutes == 20
    assert combined.max_minutes == 90


def test_playtime_overlap_true():
    a = Playtime(min_minutes=30, max_minutes=60)
    b = Playtime(min_minutes=45, max_minutes=90)
    assert playtime_overlap(a, b) is True


def test_playtime_overlap_false():
    a = Playtime(min_minutes=10, max_minutes=20)
    b = Playtime(min_minutes=30, max_minutes=40)
    assert playtime_overlap(a, b) is False


def test_parse_two_digit_groups():
    pt = parse_playtime("20 to 40 min")
    assert pt.min_minutes == 20
    assert pt.max_minutes == 40
