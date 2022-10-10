import os
import sys
import argparse
from sfzparser import SFZFile
from utils import group_by_attr
import itertools
from collections import defaultdict

parser = argparse.ArgumentParser(
    description='quantize and compress SFZ files'
)
parser.add_argument('files', type=str, help='files to process', nargs='+')
args = parser.parse_args()


def quantize_pitch(regions, pitch_levels=25):
    lowestkey = min(map(lambda x: int(x.attributes['key']), regions))
    highestkey = max(map(lambda x: int(x.attributes['key']), regions))

    keyspan = highestkey - lowestkey
    pitch_skip = keyspan / pitch_levels

    evenly_divided = \
        int(keyspan / pitch_levels) == float(keyspan) / float(pitch_levels)

    # a dict of sample_pitch -> [lokey, hikey, pitch_keycenter]
    pitchmapping = {}
    for key in range(
            lowestkey + (pitch_skip / 2),
            highestkey + 1 + (pitch_skip / 2),
            pitch_skip):
        pitchmapping[key] = {
            'lokey': key - (pitch_skip / 2),
            'pitch_keycenter': key,
            'hikey': key + (pitch_skip / 2) - (0 if evenly_divided else 1),
        }

    for key, regions in group_by_attr(regions, 'key').items():
        if int(key) in pitchmapping:
            for region in regions:
                region.attributes.update(pitchmapping[int(key)])
                del region.attributes['key']
                yield region


def quantize_velocity(regions, velocity_levels=5):
    lowestvel = min(map(lambda x: int(x.attributes['xfin_loivel']), regions))
    highestvel = max(map(lambda x: int(x.attributes['xfin_hivel']), regions))

    velspan = 127
    pitch_skip = velspan / velocity_levels

    evenly_divided = \
        int(keyspan / pitch_levels) == float(keyspan) / float(pitch_levels)

    # a dict of sample_pitch -> [lokey, hikey, pitch_keycenter]
    pitchmapping = {}
    for key in range(
            lowestkey + (pitch_skip / 2),
            highestkey + 1 + (pitch_skip / 2),
            pitch_skip):
        pitchmapping[key] = {
            'lokey': key - (pitch_skip / 2),
            'pitch_keycenter': key,
            'hikey': key + (pitch_skip / 2) - (0 if evenly_divided else 1),
        }

    for key, regions in group_by_attr(regions, 'key').items():
        if int(key) in pitchmapping:
            for region in regions:
                region.attributes.update(pitchmapping[int(key)])
                del region.attributes['key']
                yield region


def compute_sample_size(filename, regions):
    size = 0

    for region in regions:
        fullpath = os.path.join(
            os.path.dirname(filename),
            region.attributes['sample']
        )
        size += os.stat(fullpath).st_size
    return size


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='flac-ize SFZ files into one sprite sample'
    )
    parser.add_argument('files', type=str, help='files to process', nargs='+')
    args = parser.parse_args()

    for filename in args.files:
        groups = SFZFile(open(filename).read()).groups
        sys.stderr.write(
            "Original sample size: %d bytes\n" %
            compute_sample_size(
                filename,
                sum([group.regions for group in groups], [])
            )
        )
        regions = sum([group.regions for group in groups], [])
        output = list(quantize_pitch(regions))
        sys.stderr.write(
            "Quantized sample size: %d bytes\n" %
            compute_sample_size(
                filename,
                output
            )
        )
        for region in output:
            print region
        # for group in groups:
        #     print group
