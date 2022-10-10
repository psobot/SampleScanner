import time
import numpy
from .utils import note_name, percent_to_db
from .record import record
from .consts import CLIPPING_THRESHOLD, \
    CLIPPING_CHECK_NOTE, \
    EXIT_ON_CLIPPING, \
    SAMPLE_RATE
from .midi_helpers import all_notes_off, CHANNEL_OFFSET


def generate_sample(
    limit,
    midiout,
    note,
    velocity,
    midi_channel,
    threshold,
    print_progress=False,
    audio_interface_name=None,
    sample_rate=SAMPLE_RATE,
):
    all_notes_off(midiout, midi_channel)

    def after_start():
        midiout.send_message([
            CHANNEL_OFFSET + midi_channel, note, velocity
        ])

    def on_time_up():
        midiout.send_message([
            CHANNEL_OFFSET + midi_channel, note, 0
        ])
        return True  # Get the release after keyup

    return record(
        limit=limit,
        after_start=after_start,
        on_time_up=on_time_up,
        threshold=threshold,
        print_progress=print_progress,
        audio_interface_name=audio_interface_name,
        sample_rate=sample_rate,
    )


def sample_threshold_from_noise_floor(bit_depth, audio_interface_name):
    time.sleep(1)
    print("Sampling noise floor...")
    sample_width, data, release_time = record(
        limit=2.0,
        after_start=None,
        on_time_up=None,
        threshold=0.1,
        print_progress=True,
        allow_empty_return=True,
        audio_interface_name=audio_interface_name,
    )
    noise_floor = (
        numpy.amax(numpy.absolute(data)) /
        float(2 ** (bit_depth - 1))
    )
    print("Noise floor has volume %8.8f dBFS" % percent_to_db(noise_floor))
    threshold = noise_floor * 1.1
    print("Setting threshold to %8.8f dBFS" % percent_to_db(threshold))
    return threshold


def check_for_clipping(
    midiout,
    midi_channel,
    threshold,
    bit_depth,
    audio_interface_name,
):
    time.sleep(1)
    print("Checking for clipping and balance on note %s..." % (
        note_name(CLIPPING_CHECK_NOTE)
    ))

    sample_width, data, release_time = generate_sample(
        limit=2.0,
        midiout=midiout,
        note=CLIPPING_CHECK_NOTE,
        velocity=127,
        midi_channel=midi_channel,
        threshold=threshold,
        print_progress=True,
        audio_interface_name=audio_interface_name,
    )

    if data is None:
        raise Exception(
            "Can't check for clipping because all we recorded was silence.")

    max_volume = (
        numpy.amax(numpy.absolute(data)) /
        float(2 ** (bit_depth - 1))
    )

    # All notes off, but like, a lot, again
    for _ in range(0, 2):
        all_notes_off(midiout, midi_channel)

    print("Maximum volume is around %8.8f dBFS" % percent_to_db(max_volume))
    if max_volume >= CLIPPING_THRESHOLD:
        print("Clipping detected (%2.2f dBFS >= %2.2f dBFS) at max volume!" % (
            percent_to_db(max_volume), percent_to_db(CLIPPING_THRESHOLD)
        ))
        if EXIT_ON_CLIPPING:
            raise ValueError("Clipping detected at max volume!")

    # TODO: Finish implementing left/right balance check.
    #
    # max_volume_per_channel = [(
    #     numpy.amax(numpy.absolute(data)) /
    #     float(2 ** (bit_depth - 1))
    # ) for channel in data]
    # avg_volume = (
    #     float(sum(max_volume_per_channel)) /
    #     float(len(max_volume_per_channel))
    # )
    # print 'avg', avg_volume
    # print 'max', max_volume_per_channel
    # volume_diff_per_channel = [
    #     float(x) / avg_volume for x in max_volume_per_channel
    # ]

    # if any([x > VOLUME_DIFF_THRESHOLD for x in volume_diff_per_channel]):
    #     print "Balance is skewed! Expected 50/50 volume, got %2.2f/%2.2f" % (
    #         volume_diff_per_channel[0] * 100,
    #         volume_diff_per_channel[1] * 100,
    #     )
    #     if EXIT_ON_BALANCE_BAD:
    #         raise ValueError("Balance skewed!")
    # time.sleep(1)


def fundamental_frequency(list, sampling_rate=1):
    w = numpy.fft.rfft(list)
    freqs = numpy.fft.fftfreq(len(w))

    # Find the peak in the coefficients
    # idx = numpy.argmax(numpy.abs(w[:len(w) / 2]))
    idx = numpy.argmax(numpy.abs(w))
    freq = freqs[idx]
    return abs(freq * sampling_rate)
