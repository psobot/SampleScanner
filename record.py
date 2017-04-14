#!/usr/bin/env python
import argparse
from lib.utils import note_number
from lib.send_notes import sample_program, VELOCITIES, MAX_ATTEMPTS


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='create SFZ files from external audio devices'
    )
    sampling_options = parser.add_argument_group('Sampling Options')
    sampling_options.add_argument(
        '--program-number', type=int,
        help='switch to a program number before recording')
    sampling_options.add_argument(
        '--low-key', type=note_number, default=21,
        help='key to start sampling from (key name, octave number)')
    sampling_options.add_argument(
        '--high-key', type=note_number, default=109,
        help='key to stop sampling at (key name, octave number)')
    sampling_options.add_argument(
        '--velocity-levels', type=int, default=VELOCITIES, nargs='+',
        help='velocity levels (in [1, 127]) to sample')
    sampling_options.add_argument(
        '--key-skip', type=int, default=1, dest='key_range',
        help='number of keys covered by one sample')
    sampling_options.add_argument(
        '--max-attempts', type=int, default=MAX_ATTEMPTS,
        help='maximum number of tries to resample a note')
    sampling_options.add_argument(
        '--limit', type=float, default=45,
        help='length in seconds of longest sample')
    sampling_options.add_argument(
        '--has-portamento', action='store_true', dest='has_portamento',
        help='play each note once before sampling to avoid '
             'portamento sweeps between notes')
    sampling_options.add_argument(
        '--sample-asc', action='store_true', dest='sample_asc',
        help='sample notes from low to high (default false)')

    output_options = parser.add_argument_group('Output Options')
    output_options.add_argument(
        'output_folder', type=str,
        help='name of output folder')
    output_options.add_argument(
        '--no-flac', action='store_false', dest='flac',
        help="don't compress output to flac samples")
    output_options.add_argument(
        '--no-delete', action='store_false', dest='cleanup_aif_files',
        help='leave temporary .aif files in place after flac compression')
    output_options.add_argument(
        '--loop', action='store_true', dest='looping_enabled',
        help='attempt to loop sounds (should only be used '
             'with sounds with infinite sustain)')

    io_options = parser.add_argument_group('MIDI/Audio IO Options')
    io_options.add_argument(
        '--midi-port-name', type=str,
        help='name of MIDI device to use')
    io_options.add_argument(
        '--midi-port-index', type=int, default=-1,
        help='index of MIDI device to use')
    io_options.add_argument(
        '--midi-channel', type=int, default=1,
        help='MIDI channel to send messages on')
    io_options.add_argument(
        '--audio-interface-name', type=str,
        help='name of audio input device to use')
    io_options.add_argument(
        '--audio-interface-index', type=int, default=-1,
        help='index of audio input device to use')
    io_options.add_argument(
        '--sample-rate', type=int, default=48000,
        help='sample rate to use. audio interface must support this rate.')

    misc_options = parser.add_argument_group('Misc Options')
    misc_options.add_argument(
        '--print-progress', action='store_true', dest='print_progress',
        help='show text-based VU meters in terminal (default false, '
             'can cause audio artifacts)')

    args = parser.parse_args()

    sample_program(
        output_folder=args.output_folder,
        low_key=args.low_key,
        high_key=args.high_key,
        max_attempts=args.max_attempts,
        midi_channel=args.midi_channel,
        midi_port_name=args.midi_port_name,
        midi_port_index=args.midi_port_index,
        audio_interface_name=args.audio_interface_name,
        audio_interface_index=args.audio_interface_index,
        program_number=args.program_number,
        flac=args.flac,
        velocity_levels=args.velocity_levels,
        key_range=args.key_range,
        cleanup_aif_files=args.cleanup_aif_files,
        limit=args.limit,
        looping_enabled=args.looping_enabled,
        print_progress=args.print_progress,
        has_portamento=args.has_portamento,
        sample_asc=args.sample_asc,
        sample_rate=args.sample_rate,
    )
