import sys
import numpy
from struct import pack
from math import sqrt
from constants import bit_depth, NUMPY_DTYPE, SAMPLE_RATE
from utils import percent_to_db

import pyaudio
import wave

CHUNK_SIZE = 1024
NUM_CHANNELS = 2
FORMAT = pyaudio.paInt16 if bit_depth == 16 else pyaudio.paInt24

GO_UP = "\033[F"
ERASE = "\033[2K"


def is_silent(snd_data, threshold):
    maxval = max(
        abs(numpy.amax(snd_data)),
        abs(numpy.amin(snd_data))
    ) / float(2 ** (bit_depth - 1))
    return maxval < threshold


def get_input_device_names(py_audio, info):
    input_interface_names = {}
    for i in range(0, info.get('deviceCount')):
        device_info = py_audio.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            input_interface_names[i] = device_info.get('name')
    return input_interface_names


def get_input_device_index(py_audio, audio_interface_name=None):
    info = py_audio.get_host_api_info_by_index(0)
    input_interface_names = get_input_device_names(py_audio, info)

    if audio_interface_name:
        for index, name in input_interface_names.iteritems():
            if audio_interface_name.lower() in name.lower():
                return index
        else:
            raise Exception(
                "Could not find audio input '%s' in inputs:\n%s" % (
                    audio_interface_name,
                    list_input_devices(input_interface_names)))


def get_input_device_name_by_index(audio_interface_index):
    py_audio = pyaudio.PyAudio()
    info = py_audio.get_host_api_info_by_index(0)
    input_interface_names = get_input_device_names(py_audio, info)

    for index, name in input_interface_names.iteritems():
        if index == audio_interface_index:
            return name
    else:
        raise Exception(
            "Could not find audio input index %s in inputs:\n%s" % (
                audio_interface_index,
                list_input_devices(input_interface_names)))


def list_input_devices(device_names):
    lines = []
    for index, name in sorted(device_names.iteritems()):
        lines.append(u"{:3d}. {}".format(index, name))
    return u"\n".join(lines).encode("ascii", "ignore")


def record(
    limit=None,
    after_start=None,
    on_time_up=None,
    threshold=0.00025,
    print_progress=True,
    allow_empty_return=False,
    audio_interface_name=None,
    sample_rate=SAMPLE_RATE,
):
    p = pyaudio.PyAudio()
    input_device_index = get_input_device_index(p, audio_interface_name)

    stream = p.open(
        format=FORMAT,
        channels=NUM_CHANNELS,
        rate=sample_rate,
        input=True,
        output=False,
        frames_per_buffer=CHUNK_SIZE,
        input_device_index=input_device_index
    )

    num_silent = 0
    silence_timeout = sample_rate * 2.0
    snd_started = False
    in_tail = False
    release_time = None

    if print_progress:
        sys.stderr.write("\n")

    peak_value = None
    peak_index = None

    data = []
    total_length = 0

    while 1:
        if total_length > 0 and after_start is not None:
            after_start()
            after_start = None  # don't call back again
        array = stream.read(CHUNK_SIZE)
        snd_data = numpy.fromstring(array, dtype=NUMPY_DTYPE)
        snd_data = numpy.reshape(snd_data, (2, -1), 'F')

        peak_in_buffer = numpy.amax(numpy.absolute(snd_data), 1)
        peak_in_buffer_idx = numpy.argmax(numpy.absolute(snd_data))
        mono_peak_in_buffer = max(peak_in_buffer)

        if peak_value is None or peak_value < mono_peak_in_buffer:
            peak_value = mono_peak_in_buffer
            peak_index = total_length + peak_in_buffer_idx

        data.append(snd_data)
        total_length += len(snd_data[0])
        total_duration_seconds = float(total_length) / sample_rate

        time_since_peak = total_length - peak_index
        peak_pct = mono_peak_in_buffer / peak_value
        if time_since_peak:
            estimated_remaining_duration = peak_pct / time_since_peak
        else:
            estimated_remaining_duration = 1

        if print_progress:
            raw_percentages = (
                peak_in_buffer.astype(numpy.float) /
                float(2 ** (bit_depth - 1))
            )
            dbfs = [percent_to_db(x) for x in raw_percentages]
            pct_loudness = [min(1, max(0, 1 + db / 100.)) for db in dbfs]
            sys.stderr.write(ERASE)
            sys.stderr.write("\t%2.2f secs\t" % total_duration_seconds)
            sys.stderr.write("% 7.2f dBFS\t\t|%s%s|\n" % (
                dbfs[0],
                int(40 * pct_loudness[0]) * '=',
                int(40 * (1 - pct_loudness[0])) * ' ',
            ))
            sys.stderr.write(ERASE)
            sys.stderr.write("\t\t\t% 7.2f dBFS\t\t|%s%s|\n" % (
                dbfs[1],
                int(40 * pct_loudness[1]) * '=',
                int(40 * (1 - pct_loudness[1])) * ' ',
            ))
            pct_silence_end = float(num_silent) / silence_timeout
            estimated_remaining_duration_string = \
                "est. remaining duration: %2.2f secs" % (
                    estimated_remaining_duration
                )
            if in_tail:
                sys.stderr.write(ERASE)
                sys.stderr.write("\t\treleasing\t\tsilence:|%s%s| %s" % (
                    int(40 * pct_silence_end) * '=',
                    int(40 * (1 - pct_silence_end)) * ' ',
                    estimated_remaining_duration_string,
                ))
            else:
                sys.stderr.write(ERASE)
                sys.stderr.write("\t\t\t\t\tsilence:|%s%s| %s" % (
                    int(40 * pct_silence_end) * '=',
                    int(40 * (1 - pct_silence_end)) * ' ',
                    estimated_remaining_duration_string,
                ))
            sys.stderr.write(GO_UP)
            sys.stderr.write(GO_UP)

        silent = is_silent(snd_data, threshold)

        if silent:
            num_silent += CHUNK_SIZE
        elif not snd_started:
            snd_started = True
        else:
            num_silent = 0

        if num_silent > silence_timeout:
            if on_time_up is not None:
                on_time_up()
            break
        elif not in_tail \
                and limit is not None \
                and total_duration_seconds >= limit:
            if on_time_up is not None:
                if on_time_up():
                    num_silent = 0
                    in_tail = True
                    release_time = total_duration_seconds
                else:
                    break
            else:
                break

    if print_progress:
        sys.stderr.write("\n\n\n")

    # TODO this is inefficient, should preallocate a huge
    # array up front and then just copy into it maybe?
    # but not in the tight loop, what if that causes the clicks?
    r = numpy.empty([NUM_CHANNELS, 0], dtype=NUMPY_DTYPE)
    for chunk in data:
        r = numpy.concatenate((r, chunk), axis=1)

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    if snd_started or allow_empty_return:
        return sample_width, r, release_time
    else:
        return sample_width, None, release_time


def record_to_file(
    path,
    limit,
    after_start=None,
    on_time_up=None,
    sample_rate=SAMPLE_RATE
):
    sample_width, data, release_time = record(
        limit,
        after_start,
        on_time_up,
        sample_rate,
    )
    if data is not None:
        save_to_file(path, sample_width, data, sample_rate)
        return path
    else:
        return None


def save_to_file(path, sample_width, data, sample_rate=SAMPLE_RATE):
    wf = wave.open(path, 'wb')
    wf.setnchannels(NUM_CHANNELS)
    wf.setsampwidth(sample_width)
    wf.setframerate(sample_rate)

    flattened = numpy.asarray(data.flatten('F'), dtype=NUMPY_DTYPE)

    write_chunk_size = 512
    for chunk_start in xrange(0, len(flattened), write_chunk_size):
        chunk = flattened[chunk_start:chunk_start + write_chunk_size]
        packstring = '<' + ('h' * len(chunk))
        wf.writeframes(pack(packstring, *chunk))
    wf.close()


if __name__ == '__main__':
    print record_to_file('./demo.wav', sys.argv[1] if sys.argv[1] else None)
    print("done - result written to demo.wav")
