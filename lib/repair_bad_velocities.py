import os
import argparse
from sfzparser import SFZFile, Group
from utils import group_by_attr
from volume_leveler import level_volume


def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z


def repair_key(regions):
    # Assume the hivel is correct, and remap the lovel to be the next lowest.
    velocities = sorted([
        int(region.attributes['hivel']) for region in regions
    ])

    for region in regions:
        attrs = region.attributes
        hivel = int(attrs['hivel'])
        idx_of_lovel = velocities.index(hivel) - 1
        if idx_of_lovel >= 0:
            region.attributes['lovel'] = str(velocities[idx_of_lovel] + 1)
        else:
            region.attributes['lovel'] = str(1)
        yield region


def repair_group(group, should_level_volume=False, dirname=None):
    grouped_regions = group_by_attr(group.regions, ['key', 'pitch_keycenter'])

    regions = []

    for key, regions in grouped_regions.iteritems():
        fixed_regions = sum([list(repair_key(regions))], [])
        if level_volume:
            leveled_group = level_volume(fixed_regions, dirname)
            attrs = group.attributes.copy()
            for k in attrs.keys():
                if k.startswith('amp_velcurve_'):
                    del attrs[k]
            yield Group(
                merge_two_dicts(attrs, leveled_group.attributes),
                leveled_group.regions
            )
        else:
            yield Group(group.attributes, fixed_regions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='repair incorrect velocity mappings in sfz files'
    )
    parser.add_argument('files', type=str, help='files to process', nargs='+')
    parser.add_argument(
        '--level-volume', action='store_true', dest='level_volume',
        help='apply volume leveling to the output')
    args = parser.parse_args()

    for filename in args.files:
        dirname = os.path.dirname(filename)
        sfz = SFZFile(open(filename).read())
        for group in sfz.groups:
            for repaired in repair_group(group, args.level_volume, dirname):
                print repaired
        # with open(filename + ".repaired.sfz", 'w') as f:
        #     for group in sfz.groups:
        #         for repaired in repair_group(group, args.level_volume):
        #             f.write(repaired)
        #             f.write("\n")
