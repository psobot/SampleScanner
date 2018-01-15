import os
import argparse
from sfzparser import SFZFile
from utils import one_of

from xml.sax.saxutils import escape

FILE_HEADER = """
<?xml version="1.0" encoding="UTF-8"?>

<samplemap ID="%s" SaveMode="1" RRGroupAmount="1" MicPositions=";">"""

FILE_FOOTER = """</samplemap>"""

SAMPLE_TEMPLATE = """
  <sample ID="%s" FileName="%s"
          Root="%s" HiKey="%s" LoKey="%s" LoVel="%s" HiVel="%s" RRGroup="1"
          Volume="0" Pan="0" Normalized="0" Pitch="0" SampleStart="%s"
          SampleEnd="%s"
          SampleStartMod="0" LoopStart="%s" LoopEnd="%s" LoopXFade="0"
          LoopEnabled="%s" LowerVelocityXFade="0" UpperVelocityXFade="0"
          SampleState="0" NormalizedPeak="-1" Duplicate="0"/>"""


def region_to_sample(i, sfz_file, region):
    # HISE expects sample paths in this format:
    #   {PROJECT_FOLDER}<xml_encoded_subfolder_name>/<sample_with_ext>"
    full_file_path = "{PROJECT_FOLDER}%s/%s" % (
        escape(sfz_file.split("/")[-2]),
        os.path.split(region.attributes['sample'])[-1]
    )

    pitch_keycenter = one_of(region.attributes, 'pitch_keycenter', 'key')
    lokey = one_of(region.attributes, 'lokey', 'key')
    hikey = one_of(region.attributes, 'hikey', 'key')

    lovel = region.attributes['lovel']
    hivel = region.attributes['hivel']

    sample_start = region.attributes['offset']
    sample_end = region.attributes['end']

    loop_start = one_of(region.attributes, 'loop_start', 'offset')
    loop_end = one_of(region.attributes, 'loop_end', 'end')
    loop_enabled = region.attributes.get('loop_mode', '') == 'loop_continuous'

    return SAMPLE_TEMPLATE % (
        i,
        full_file_path,
        pitch_keycenter,
        hikey,
        lokey,
        lovel,
        hivel,
        sample_start,
        sample_end,
        loop_start,
        loop_end,
        '1' if loop_enabled else '0',
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='convert an sfz file into a HISE sample map')
    parser.add_argument(
        'file',
        type=str,
        help='sfz file to process')
    args = parser.parse_args()

    program_name = " ".join(os.path.basename(args.file).split(".")[:-1])

    print FILE_HEADER % (escape(program_name),)
    all_regions = sum(
        [
            group.flattened_regions()
            for group in SFZFile(open(args.file).read()).groups],
        [])
    for (i, region) in enumerate(all_regions):
        print region_to_sample(i, args.file, region)
    print FILE_FOOTER
