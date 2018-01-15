import numpy
import argparse
from constants import bit_depth
from sfzparser import SFZFile, Group
from wavio import read_wave_file
from utils import group_by_attr
from itertools import tee, izip
from utils import full_path


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def max_amp(filename):
    return numpy.amax(read_wave_file(filename)) / (2. ** (bit_depth - 1))


def peak_rms(data, window_size=480, limits=960):
    index = max([numpy.argmax(channel) for channel in data])
    maxlimit = max([len(channel) for channel in data])
    max_so_far = 0
    for i in xrange(
        max(index - limits, (window_size / 2)),
        min(index + limits, maxlimit - (window_size / 2))
    ):
        for channel in data:
            window = channel[i - (window_size / 2):i + (window_size / 2)]
            if len(window) == 0:
                raise Exception("Cannot take mean of empty slice! Channel "
                                "size %d, index %d, window size %d" % (
                                    len(channel), i, window_size
                                ))
            it_max = numpy.sqrt(
                numpy.mean(window.astype(numpy.float) ** 2)
            ) / (2. ** (bit_depth - 1))
            if it_max > max_so_far:
                max_so_far = it_max
    return max_so_far


REMOVE_ATTRS = ['amp_velcurve_127', 'amp_velcurve_0', 'amp_veltrack']


def level_volume(regions, dirname):
    if len(regions) == 0:
        return None

    velcurve = {}

    velsorted = list(reversed(
        sorted(regions, key=lambda x: int(x.attributes['hivel']))
    ))
    for high, low in pairwise(velsorted):
        try:
            diff = (
                peak_rms(
                    read_wave_file(
                        full_path(dirname, low.attributes['sample'])
                    )
                ) /
                peak_rms(
                    read_wave_file(
                        full_path(dirname, high.attributes['sample'])
                    )
                )
            )
        except ZeroDivisionError:
            print "Got ZeroDivisionError with high sample path: %s" % \
                high.attributes['sample']
            raise
        for attr in REMOVE_ATTRS:
            if attr in high.attributes:
                del high.attributes[attr]
        velcurve.update({
            ('amp_velcurve_%d' %
                int(high.attributes['hivel'])): 1,
            ('amp_velcurve_%d' %
                int(high.attributes['lovel'])): diff,
        })
    # print the last region that didn't have a lower counterpart
    low = velsorted[-1]
    for attr in REMOVE_ATTRS:
        if attr in low.attributes:
            del low.attributes[attr]
    velcurve.update({
        ('amp_velcurve_%d' %
            int(low.attributes['hivel'])): 1,
        ('amp_velcurve_%d' %
            int(low.attributes['lovel'])): 0,
    })
    return Group(velcurve, velsorted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='volume-level sfz files with non-normalized samples'
    )
    parser.add_argument('files', type=str, help='files to process', nargs='+')
    args = parser.parse_args()

    for filename in args.files:
        sfz = SFZFile(open(filename).read())
        regions = sum([group.regions for group in sfz.groups], [])
        for key, regions in group_by_attr(regions, 'key').iteritems():
            print level_volume(regions)
