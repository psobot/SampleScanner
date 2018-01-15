import os
import wave
import argparse
import subprocess
from tqdm import tqdm
from sfzparser import SFZFile
from wavio import read_wave_file
from utils import normalized, note_name, one_of
from record import save_to_file
from constants import bit_depth


def full_path(sfzfile, filename):
    if os.path.isdir(sfzfile):
        return os.path.join(sfzfile, filename)
    else:
        return os.path.join(os.path.dirname(sfzfile), filename)


def length_of(filename):
    return wave.open(filename).getnframes()


def decode_flac(input_filename, output_filename):
    commandline = [
        'ffmpeg',
        '-y',
        '-i',
        input_filename,
        output_filename
    ]
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


def split_sample(region,
                 path,
                 normalize=False,
                 verbose_names=True,
                 note_numbers=True):
    note = one_of(region.attributes, 'pitch_keycenter', 'key')
    if not note_numbers:
        note = note_name(note)

    if verbose_names:
        lokey = one_of(region.attributes, 'lokey', 'key')
        if not note_numbers:
            lokey = note_name(lokey)

        hikey = one_of(region.attributes, 'hikey', 'key')
        if not note_numbers:
            hikey = note_name(hikey)

        new_file_name = "%s_%s_%s_%s_%s.wav" % (
            lokey,
            hikey,
            note,
            region.attributes['lovel'],
            region.attributes['hivel']
        )
    else:
        new_file_name = "%s_v%s.wav" % (
            note,
            region.attributes['hivel']
        )

    output_file_path = full_path(path, new_file_name)
    if not os.path.isfile(output_file_path):
        decode_flac(
            full_path(path, region.attributes['sample']),
            output_file_path
        )
        data = read_wave_file(output_file_path, True)
        data = data[:,
                    int(region.attributes['offset']):
                    int(region.attributes['end']) + ANTI_CLICK_OFFSET]
        save_to_file(output_file_path, len(data), data)
        if normalize:
            normalize_file(output_file_path)

    del region.attributes['offset']
    del region.attributes['end']
    region.attributes['sample'] = new_file_name

    return region


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
    parser.add_argument(
        '--verbose-names', action='store_true', dest='verbose_names',
        help='include low velocity and low/high pitch in file name')
    args = parser.parse_args()

    all_regions = [
        group
        for filename in args.files
        for group in SFZFile(open(filename).read()).groups
    ]
    for group in tqdm(all_regions, desc='De-flacing...'):
        print group.just_group()
        for regions in group.regions:
            print split_sample(
                regions,
                filename,
                verbose_names=args.verbose_names)
