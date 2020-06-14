import os
import wave
import numpy
import subprocess

from .constants import NUMPY_DTYPE


def read_flac_file(filename, use_numpy=False):
    tempfile = filename + '.tmp.wav'
    commandline = [
        'ffmpeg',
        '-y',
        '-i',
        filename,
        tempfile
    ]
    # sys.stderr.write("Calling '%s'...\n" % ' '.join(commandline))
    subprocess.call(
        commandline,
        stdout=open('/dev/null', 'w'),
        stderr=open('/dev/null', 'w')
    )
    result = read_wave_file(tempfile, use_numpy)
    os.unlink(tempfile)
    return result


def read_wave_file(filename, use_numpy=False):
    try:
        w = wave.open(filename)
        a = numpy.fromstring(w.readframes(9999999999), dtype=NUMPY_DTYPE)
        if use_numpy:
            return numpy.reshape(a, (w.getnchannels(), -1), 'F')
        else:
            return [
                a[i::w.getnchannels()]
                for i in range(w.getnchannels())
            ]
    except wave.Error:
        print("Could not open %s" % filename)
        raise
