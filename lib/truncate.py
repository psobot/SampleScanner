import sys

from .wavio import read_wave_file
from .utils import start_of, end_of


def chop(aif):
    file = read_wave_file(aif)
    start, end = min([start_of(chan) for chan in file]), \
        max([end_of(chan) for chan in file])
    print(aif, start, end, float(end) / len(file[0]))

    # outfile = aif + '.chopped.aif'
    # r = wave.open(aif, 'rb')
    # w = wave.open(outfile, 'wb')
    # w.setnchannels(r.getnchannels())
    # w.setsampwidth(r.getsampwidth())
    # w.setframerate(r.getframerate())

    # # Seek forward to the start point
    # r.readframes(start)

    # # Copy the frames from in to out
    # w.writeframes(r.readframes(end - start))
    # r.close()
    # w.close()

    # plt.plot(file[0][:(44100 * 2)])
    # plt.axvline(start)
    # plt.axvline(end)
    # plt.show()


if __name__ == "__main__":
    chop(sys.argv[1])
