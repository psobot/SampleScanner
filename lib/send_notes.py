import os
import time
from tqdm import tqdm
from record import save_to_file
from sfzparser import SFZFile, Region
from utils import trim_data, \
    note_name, \
    first_non_none, \
    warn_on_clipping
from constants import bit_depth, SAMPLE_RATE
from volume_leveler import level_volume
from flacize import flacize_after_sampling
from loop import find_loop_points
from collections import defaultdict
from midi_helpers import all_notes_off, open_midi_port, CHANNEL_OFFSET
from audio_helpers import sample_threshold_from_noise_floor, \
    generate_sample, \
    check_for_clipping

VELOCITIES = [
    15, 44,
    63, 79, 95, 111,
    127
]
MAX_ATTEMPTS = 8
PRINT_SILENCE_WARNINGS = False

PORTAMENTO_PRESAMPLE_LIMIT = 2.0
PORTAMENTO_PRESAMPLE_WAIT = 1.0

# percentage - how much left/right delta can we tolerate?
VOLUME_DIFF_THRESHOLD = 0.01


def filename_for(note, velocity):
    return '%s_v%s.aif' % (note_name(note), velocity)


def generate_region(note, velocity, velocities, keys=None, loop=None):
    velocity_index = velocities.index(velocity)
    if velocity_index > 0:
        lovel = velocities[velocity_index - 1] + 1
    else:
        lovel = 1
    hivel = velocity

    # Note: the velcurve should be:
    #   Velocity  | Amplitude
    #   ---------------------
    #   hivel     | 1.0 (sample at full volume)
    #   ...       | linear mapping
    #   lovel + 1 | (next lowest layer's dB / this layer's dB)

    attributes = {
        'lovel': lovel,
        'hivel': hivel,
        'ampeg_release': 1,
        'sample': filename_for(note, velocity),
        'offset': 0,
    }

    if loop is not None:
        attributes.update({
            'loop_mode': 'loop_continuous',
            'loop_start': loop[0],
            'loop_end': loop[1],
        })

    if keys is None or len(keys) == 1:
        attributes['key'] = note
    else:
        attributes.update({
            'lokey': min(keys),
            'hikey': max(keys),
            'pitch_keycenter': note,
        })

    return Region(attributes)


def all_notes(notes, velocities, ascending=False):
    for note in (notes if ascending else reversed(notes)):
        for i, velocity in enumerate(velocities):
            yield note, velocity, (i == len(velocities) - 1)


CLICK_RETRIES = 5


def generate_and_save_sample(
    limit,
    midiout,
    note,
    velocity,
    midi_channel,
    filename,
    threshold,
    velocity_levels,
    keys,
    looping_enabled=False,
    print_progress=False,
    audio_interface_name=None,
    sample_rate=SAMPLE_RATE,
):
    while True:
        sample_width, data, release_time = generate_sample(
            limit=limit,
            midiout=midiout,
            note=note,
            velocity=velocity,
            midi_channel=midi_channel,
            threshold=threshold,
            print_progress=print_progress,
            audio_interface_name=audio_interface_name,
            sample_rate=sample_rate,
        )

        if data is not None:
            data = trim_data(data, threshold * 10, threshold)
            warn_on_clipping(data)
            if looping_enabled:
                loop = find_loop_points(data, SAMPLE_RATE)
            else:
                loop = None
            save_to_file(filename, sample_width, data, sample_rate)
            return generate_region(
                note, velocity, velocity_levels,
                keys, loop
            )
        else:
            return None


def sample_program(
    output_folder='foo',
    low_key=21,
    high_key=109,
    max_attempts=8,
    midi_channel=1,
    midi_port_name=None,
    audio_interface_name=None,
    program_number=None,
    flac=True,
    velocity_levels=VELOCITIES,
    key_range=1,
    cleanup_aif_files=True,
    limit=None,
    looping_enabled=False,
    print_progress=False,
    has_portamento=False,
    sample_asc=False,
    sample_rate=SAMPLE_RATE,
):
    if (key_range % 2) != 1:
        raise NotImplementedError("Key skip must be an odd number for now.")

    midiout = open_midi_port(midi_port_name)

    path_prefix = output_folder
    if program_number is not None:
        print "Sampling program number %d into path %s" % (
            program_number, output_folder
        )
    else:
        print "Sampling into path %s" % (output_folder)

    try:
        os.mkdir(path_prefix)
    except OSError:
        pass

    sfzfile = os.path.join(path_prefix, 'file.sfz')
    try:
        regions = sum([group.regions
                       for group in SFZFile(open(sfzfile).read()).groups],
                      [])
        regions = [region for region in regions if region.exists(path_prefix)]
    except IOError:
        regions = []

    if program_number is not None:
        print "Sending program change to program %d..." % program_number
        midiout.send_message([
            CHANNEL_OFFSET + midi_channel, 0xC0, program_number
        ])

    # All notes off, but like, a lot
    for _ in xrange(0, 2):
        all_notes_off(midiout, midi_channel)

    threshold = sample_threshold_from_noise_floor(
        bit_depth,
        audio_interface_name
    )

    check_for_clipping(
        midiout,
        midi_channel,
        threshold,
        bit_depth,
        audio_interface_name
    )

    groups = []
    note_regions = []

    key_range_under = key_range / 2
    key_range_over = key_range / 2
    notes_to_sample = range(
        low_key,
        (high_key - key_range_over) + 1,
        key_range
    )

    for note, velocity, done_note in tqdm(list(all_notes(
        notes_to_sample,
        velocity_levels,
        sample_asc
    ))):
        keys = range(note + key_range_under, note + key_range_over + 1)
        if not keys:
            keys = [note]
        already_sampled_region = first_non_none([
            region for region in regions
            if region.attributes['hivel'] == str(velocity) and
            region.attributes.get(
                'key', region.attributes.get(
                    'pitch_keycenter', None
                )) == str(note)])
        if already_sampled_region is None:
            filename = os.path.join(path_prefix, filename_for(note, velocity))

            if print_progress:
                print "Sampling %s at velocity %s..." % (
                    note_name(note), velocity
                )

            if has_portamento:
                sample_width, data, release_time = generate_sample(
                    limit=PORTAMENTO_PRESAMPLE_LIMIT,
                    midiout=midiout,
                    note=note,
                    velocity=velocity,
                    midi_channel=midi_channel,
                    threshold=threshold,
                    print_progress=print_progress,
                    audio_interface_name=audio_interface_name,
                    sample_rate=sample_rate,
                )
                time.sleep(PORTAMENTO_PRESAMPLE_WAIT)

            for attempt in xrange(0, MAX_ATTEMPTS):
                try:
                    region = generate_and_save_sample(
                        limit=limit,
                        midiout=midiout,
                        note=note,
                        velocity=velocity,
                        midi_channel=midi_channel,
                        filename=filename,
                        threshold=threshold,
                        velocity_levels=velocity_levels,
                        keys=keys,
                        looping_enabled=looping_enabled,
                        print_progress=print_progress,
                        audio_interface_name=audio_interface_name,
                        sample_rate=sample_rate,
                    )
                    if region:
                        regions.append(region)
                        note_regions.append(region)
                        with open(sfzfile, 'w') as file:
                            file.write("\n".join([str(r) for r in regions]))
                    elif PRINT_SILENCE_WARNINGS:
                        print "Got no sound for %s at velocity %s." % (
                            note_name(note), velocity
                        )
                except IOError:
                    pass
                else:
                    break
            else:
                print "Could not sample %s at vel %s: too many IOErrors." % (
                    note_name(note), velocity
                )
        else:
            note_regions.append(already_sampled_region)

        if done_note and len(note_regions) > 0:
            groups.append(level_volume(note_regions, output_folder))
            note_regions = []

    # Write the volume-leveled output:
    with open(sfzfile + '.leveled.sfz', 'w') as file:
        file.write("\n".join([str(group) for group in groups]))

    if flac:
        # Do a FLAC compression pass afterwards
        # TODO: Do this after each note if possible
        # would require graceful re-parsing of FLAC-combined regions
        flacize_after_sampling(
            output_folder,
            groups,
            sfzfile,
            cleanup_aif_files=True
        )
