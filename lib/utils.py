import itertools
import numpy
import math
from numpy import inf

from constants import default_silence_threshold, bit_depth
from collections import defaultdict


NOTE_NAMES = ('C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B')
C0_OFFSET = 12


def note_name(note):
    """Return a note name from the MIDI note number."""
    from_c = int(int(note) - C0_OFFSET)
    note_name = NOTE_NAMES[(from_c % 12)]
    octave_number = (from_c / 12)
    return "%s%d" % (note_name, octave_number)


def note_number(note_name):
    """Return the MIDI key number from a note name.

    The first character of ``note_name`` can be in lower or upper case.
    """
    name = note_name[0].upper()
    if len(note_name) > 2:
        name += note_name[1]
    octave_number = int(note_name[-1])
    return C0_OFFSET + NOTE_NAMES.index(name) + (12 * octave_number)


def two_ints(value):
    """Type for argparse. Demands 2 integers separated by a comma."""
    key, val = value.split(',')
    return (int(key), int(val))


def warn_on_clipping(data, threshold=0.9999):
    if numpy.amax(numpy.absolute(data)) > ((2 ** (bit_depth - 1)) * threshold):
        print("WARNING: Clipping detected!")


def sample_value_to_db(value, bit_depth=bit_depth):
    if value == 0:
        return -inf
    return 20. * math.log(float(abs(value)) / (2 ** (bit_depth - 1)), 10)


def percent_to_db(percent):
    if percent == 0:
        return -inf
    return 20. * math.log(percent, 10)


def dbfs_as_percent(dbfs, bit_depth=bit_depth):
    """
    Represent a dBFS value as a percentage, which can be used to render
    a VU meter. Note this is _not_ the inverse of percent_to_db.
    """
    minimum_dbfs_value = sample_value_to_db(1, bit_depth)
    return min(1., max(0., (dbfs / -minimum_dbfs_value) + 1))


def trim_data(
    data,
    start_threshold=default_silence_threshold,
    end_threshold=default_silence_threshold
):
    start, end = min([start_of(chan, start_threshold) for chan in data]), \
        max([end_of(chan, end_threshold) for chan in data])

    return data[0:, start:end]


def trim_mono_data(
    data,
    start_threshold=default_silence_threshold,
    end_threshold=default_silence_threshold
):
    start, end = start_of(data, start_threshold), end_of(data, end_threshold)
    return data[start:end]


def normalized(list):
    return list.astype(numpy.float32) / float(numpy.amax(numpy.abs(list)))


def start_of(list, threshold=default_silence_threshold, samples_before=1):
    if int(threshold) != threshold:
        threshold = threshold * float(2 ** (bit_depth - 1))
    index = numpy.argmax(numpy.absolute(list) > threshold)
    if index > (samples_before - 1):
        return index - samples_before
    else:
        return 0


def end_of(list, threshold=default_silence_threshold, samples_after=1):
    if int(threshold) != threshold:
        threshold = threshold * float(2 ** (bit_depth - 1))
    rev_index = numpy.argmax(
        numpy.flipud(numpy.absolute(list)) > threshold
    )
    if rev_index > (samples_after - 1):
        return len(list) - (rev_index - samples_after)
    else:
        return len(list)


def first_non_none(list):
    try:
        return next(item for item in list if item is not None)
    except StopIteration:
        return None


def group_by_attr(data, attrs):
    if not isinstance(attrs, list):
        attrs = [attrs]
    groups = defaultdict(list)
    for k, g in itertools.groupby(
        data,
        lambda x: first_non_none([
            x.attributes.get(attr, None) for attr in attrs
        ])
    ):
        groups[k].extend(list(g))
    return groups
