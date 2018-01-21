"""A few tests for pitch.py."""

from lib.pitch import compute_zones, Zone


def test_zones_with_step_1():
    total = Zone(60, 61)
    assert [
        Zone(low=60, high=60, center=60),
        Zone(low=61, high=61, center=61),
    ] == compute_zones(total, step=1)


def test_zones_with_step_2():
    total = Zone(0, 3)
    assert [
        Zone(low=0, high=1, center=1),
        Zone(low=2, high=3, center=3),
    ] == compute_zones(total, step=2)


def test_zones_with_step_2_partial():
    total = Zone(0, 2)
    assert [
        Zone(low=0, high=1, center=1),
        Zone(low=2, high=2, center=3),
    ] == compute_zones(total, step=2)


def test_zones_with_step_3():
    total = Zone(48, 55)
    assert [
        Zone(low=48, center=49, high=50),
        Zone(low=51, center=52, high=53),
        Zone(low=54, center=55, high=55),
    ] == compute_zones(total, step=3)


def test_zones_with_step_4():
    total = Zone(48, 56)
    assert [
        Zone(low=48, center=50, high=51),
        Zone(low=52, center=54, high=55),
        Zone(low=56, center=58, high=56),
    ] == compute_zones(total, step=4)
