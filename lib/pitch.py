#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Computations concerning pitch.

Let me define 2 terms:

- A "zone" is simply a pitch range -- an area of the keyboard,
  from a low key to a high key.
- A "region" is a concept of sfz that consubstantiates a *zone*, but also
  contains information about velocities (and probably more).

This module deals with pitch only -- zones, not regions.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# TODO Move here translation of 60 to "C4" etc from "utils" module.


class Zone(object):
    """Smart data structure to store 2 pitches."""

    def __init__(self, low, high, center=None):
        """Expect parameters in the range 0-127.

        Middle C is 60 and a grand piano goes from 21 to 108.

        Only in tests is the parameter "center" used in the constructor.
        In actual code it is populated after construction.
        """
        assert isinstance(low, int)
        assert isinstance(high, int)
        assert high >= low
        assert high < 128
        assert low > -1
        self.low = low
        self.high = high
        self.center = center

    @property
    def size(self):
        """Return the width of this range."""
        return self.high - self.low

    @property
    def keys(self):
        return list(range(self.low, self.high))

    def __repr__(self):
        return '<Zone low={} high={} center={}>'.format(
            self.low, self.high, self.center)

    def __eq__(self, other):
        """Compare self to ``other``. Makes test writing easier."""
        return (
            self.low == other.low
            and self.high == other.high
            and self.center == other.center)


def optimal_pitch_center(step=1):
    """Given a step size, decide where to place the pitch center.

    Preference is given to extending the region downwards -- sounds better.
    """
    assert 0 < step < 128

    def _a_generator():
        yield False
        yield True
        while True:
            yield False
            yield False
            yield True

    answer = 0
    a_generator = _a_generator()
    for _ in range(step - 1):
        if not next(a_generator):
            answer += 1
    return answer


def compute_zones(pitch_range, step):
    """Plan the keyboard zones (with their pitch centers) to cover a range.

    The param ``pitch_range`` must be a Zone instance defining the
    part of the keyboard that you want sampled.

    The param ``step`` is typically 1 (meaning sample each note) or
    3 (meaning sample in minor thirds).
    """
    assert isinstance(step, int)
    assert isinstance(pitch_range, Zone)
    pitch_center_offset = optimal_pitch_center(step)
    regions = []
    low = pitch_range.low
    while True:
        zone = Zone(low=low, high=min(low + step - 1, pitch_range.high))
        zone.center = low + pitch_center_offset
        regions.append(zone)
        low += step
        if low > pitch_range.high:
            break
    return regions
