import os
import sys
import wave
import time
import argparse
import subprocess
from tqdm import tqdm
from sfzparser import SFZFile, Group
from wavio import read_wave_file
from utils import group_by_attr, note_name


def full_path(sfzfile, filename):
    if os.path.isdir(sfzfile):
        return os.path.join(sfzfile, filename)
    else:
        return os.path.join(os.path.dirname(sfzfile), filename)


def length_of(filename):
    return wave.open(filename).getnframes()


def create_flac(concat_filename, output_filename):
    commandline = [
        'ffmpeg',
        '-y',
        '-f',
        'concat',
        '-safe',
        '0',
        '-i',
        concat_filename,
        '-c:a',
        'flac',
        '-compression_level', '12',
        output_filename
    ]
    # sys.stderr.write("Calling '%s'...\n" % ' '.join(commandline))
    subprocess.check_call(
        commandline,
        stdout=open(os.devnull, 'w'),
        stderr=subprocess.STDOUT
    )


def flacize_after_sampling(
    output_folder,
    groups,
    sfzfile,
    cleanup_aif_files=True
):
    new_groups = []

    old_paths_to_unlink = [
        full_path(output_folder, r.attributes['sample'])
        for group in groups
        for r in group.regions
    ]

    for group in groups:
        # Make one FLAC file per key, to get more compression.
        output = sum([list(concat_samples(
                           key_regions, output_folder, note_name(key)
                           ))
                      for key, key_regions in
                      group_by_attr(group.regions, [
                          'key', 'pitch_keycenter'
                      ]).iteritems()], [])
        new_groups.append(Group(group.attributes, output))

    with open(sfzfile + '.flac.sfz', 'w') as file:
        file.write("\n".join([str(group) for group in new_groups]))

    if cleanup_aif_files:
        for path in old_paths_to_unlink:
            try:
                os.unlink(path)
            except OSError as e:
                print "Could not unlink path: %s: %s" % (path, e)


ANTI_CLICK_OFFSET = 3


def concat_samples(regions, path, name=None):
    if name is None:
        output_filename = 'all_samples_%f.flac' % time.time()
    else:
        output_filename = '%s.flac' % name

    concat_filename = 'concat.txt'

    with open(concat_filename, 'w') as outfile:
        global_offset = 0
        for region in regions:
            sample = region.attributes['sample']

            sample_data = read_wave_file(full_path(path, sample))

            sample_length = len(sample_data[0])
            region.attributes['offset'] = global_offset
            region.attributes['end'] = (
                global_offset + sample_length - ANTI_CLICK_OFFSET
            )
            # TODO: make sure endpoint is a zero crossing to prevent clicks
            region.attributes['sample'] = output_filename
            outfile.write("file '%s'\n" % full_path(path, sample))
            global_offset += sample_length

    create_flac(concat_filename, full_path(path, output_filename))
    os.unlink(concat_filename)

    return regions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='flac-ize SFZ files into one sprite sample'
    )
    parser.add_argument('files', type=str, help='files to process', nargs='+')
    args = parser.parse_args()

    for filename in args.files:
        for group in SFZFile(open(filename).read()).groups:
            # Make one FLAC file per key, to get more compression.
            output = sum([list(concat_samples(regions,
                                              filename,
                                              note_name(key)))
                          for key, regions in
                          tqdm(group_by_attr(group.regions,
                                             'key').iteritems())], [])
            print group.just_group()
            for region in output:
                print region
