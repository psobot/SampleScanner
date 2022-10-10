import argparse
from sfzparser import parse, Group
from quantize import group_by_attr

parser = argparse.ArgumentParser(
    description='quantize and compress SFZ files'
)
parser.add_argument('files', type=str, help='files to process', nargs='+')
args = parser.parse_args()


def should_group_key(key):
    return (
        key.startswith('amp_velcurve_') or
        key == 'key' or
        key == 'ampeg_release'
    )


def group_by_pitch(regions):
    for key, regions in group_by_attr(regions, 'key').items():
        # Group together all amp_velcurve_* and key params.
        yield Group(dict([
            (key, value)
            for region in regions
            for key, value in region.attributes.items()
            if should_group_key(key)
        ] + DEFAULT_ATTRIBUTES.items()), [
            region.without_attributes(should_group_key) for region in regions
        ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='flac-ize SFZ files into one sprite sample'
    )
    parser.add_argument('files', type=str, help='files to process', nargs='+')
    args = parser.parse_args()

    for filename in args.files:
        groups = parse(open(filename).read())
        regions = sum([group.flattened_regions() for group in groups], [])
        for group in group_by_pitch(regions):
            print group
