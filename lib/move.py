import os
import argparse
from sfzparser import SFZFile


def move_sample(region, new_directory):
    region.attributes['sample'] = os.path.join(
        new_directory, os.path.basename(region.attributes['sample']))
    return region


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='relocate the samples in an sfz file and '
                    'keep relative paths consistent')
    parser.add_argument('directory', type=str,
                        help='new location for audio samples')
    parser.add_argument('files', type=str,
                        help='sfz files to process', nargs='+')
    args = parser.parse_args()

    for filename in args.files:
        groups = SFZFile(open(filename).read()).groups
        for group in groups:
            print group.just_group()
            for region in group.regions:
                print move_sample(region, args.directory)
