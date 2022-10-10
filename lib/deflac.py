import os
import sys
import wave
import numpy
import argparse
import subprocess
from tqdm import tqdm
from sfzparser import SFZFile
from wavio import read_wave_file
from utils import normalized
from record import RATE, save_to_file
from consts import bit_depth


def full_path(sfzfile, filename):
    if os.path.isdir(sfzfile):
        return os.path.join(sfzfile, filename)
    else:
        return os.path.join(os.path.dirname(sfzfile), filename)


def length_of(filename):
    return wave.open(filename).getnframes()


def split_flac(input_filename, start_time, end_time, output_filename):
    commandline = [
        'ffmpeg',
        '-y',
        '-i',
        input_filename,
        '-ss',
        str(start_time),
        '-to',
        str(end_time),
        output_filename
    ]
    # sys.stderr.write("Calling '%s'...\n" % ' '.join(commandline))
    subprocess.call(
        commandline,
        stdout=open('/dev/null', 'w'),
        stderr=open('/dev/null', 'w')
    )


def normalize_file(filename):
    data = read_wave_file(filename, True)
    if len(data):
        normalized_data = normalized(data) * (2 ** (bit_depth - 1) - 1)
    else:
        normalized_data = data
    save_to_file(filename, 2, normalized_data)

ANTI_CLICK_OFFSET = 3


def split_sample(region, path):
    new_file_name = "%s_%s_%s.wav" % (
        region.attributes['key'],
        region.attributes['lovel'],
        region.attributes['hivel']
    )
    output_file_path = full_path(path, new_file_name)
    if not os.path.isfile(output_file_path):
        split_flac(
            full_path(path, region.attributes['sample']),
            float(region.attributes['offset']) / float(RATE),
            float(region.attributes['end']) / float(RATE),
            output_file_path
        )
        normalize_file(output_file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='split up flac-ized SFZ file into wavs'
    )
    parser.add_argument(
        'files',
        type=str,
        help='sfz files to process',
        nargs='+'
    )
    args = parser.parse_args()

    all_regions = [
        regions
        for filename in args.files
        for group in SFZFile(open(filename).read()).groups
        for regions in group.regions
    ]
    for regions in tqdm(all_regions, desc='De-flacing...'):
        split_sample(regions, filename)
