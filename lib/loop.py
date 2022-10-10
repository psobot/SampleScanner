import sys
import numpy
from tqdm import tqdm

from .truncate import read_wave_file
from .audio_helpers import fundamental_frequency

QUANTIZE_FACTOR = 8


def compare_windows(window_a, window_b):
    return numpy.sqrt(numpy.mean(numpy.power(window_a - window_b, 2)))


def slide_window(file, period, start_at=0, end_before=0):
    for power in reversed(range(7, 10)):
        multiple = 2 ** power
        window_size = int(period * multiple)
        # Uncomment this to search from the start_at value to the end_before
        # rather than just through one window's length
        # end_range = len(file) - (window_size * 2) - end_before
        end_range = start_at + window_size
        for i in range(start_at, end_range):
            yield power, i, window_size


def window_match(file):
    period = (1.0 / fundamental_frequency(file, 1)) * 2
    print(period, 'period in samples')

    winner = None

    window_positions = list(
        slide_window(file, period, len(file) / 2, len(file) / 8)
    )
    for power, i, window_size in tqdm(window_positions):
        window_start = find_similar_sample_index(file, i, i + window_size)
        window_end = find_similar_sample_index(file, i, i + (window_size * 2))
        effective_size = window_end - window_start

        difference = compare_windows(
            file[i:i + effective_size],
            file[window_start:window_end]
        ) / effective_size
        if winner is None or difference < winner[0]:
            winner = (
                difference,
                effective_size,
                i,
                abs(file[i] - file[window_start])
            )
            print('new winner', winner)

    lowest_difference, winning_window_size, winning_index, gap = winner

    print("Best loop match:", lowest_difference)
    print("window size", winning_window_size)
    print("winning index", winning_index)
    print("winning gap", gap)
    return winning_index, winning_window_size


def slope_at_index(file, i):
    return (file[i + 1] - file[i - 1]) / 2


def find_similar_sample_index(
    file,
    reference_index,
    search_around_index,
    search_size=100  # samples
):
    reference_slope = slope_at_index(file, reference_index) > 0
    best_match = None
    search_range = range(
        search_around_index - search_size,
        search_around_index + search_size
    )
    for i in search_range:
        slope = slope_at_index(file, i) > 0
        if slope != reference_slope:
            continue

        abs_diff = abs(file[i] - file[reference_index])

        if best_match is not None:
            _, best_abs_diff = best_match
            if abs_diff < best_abs_diff:
                best_match = (i, abs_diff)
        else:
            best_match = (i, abs_diff)
    return best_match[0] if best_match is not None else search_around_index


def zero_crossing_match(file):
    period = (1.0 / fundamental_frequency(file, 1)) * 2
    print(period, 'period in samples')

    period_multiple = 64
    period = period * period_multiple

    for i in reversed(range(2 * len(file) / 3, 5 * len(file) / 6)):
        if file[i] >= 0 and file[i + 1] < 0 and \
                file[int(i + period)] >= 0 and \
                file[int(i + 1 + period)] < 0 and \
                file[int(i + period * 2)] >= 0 and \
                file[int(i + 1 + period * 2)] < 0:
            return i, int(period)


def fast_autocorrelate(x):
    """
    Compute the autocorrelation of the signal, based on the properties of the
    power spectral density of the signal.

    Note that the input's length may be reduced before the correlation is
    performed due to a pathalogical case in numpy.fft:
    http://stackoverflow.com/a/23531074/679081

    > The FFT algorithm used in np.fft performs very well (meaning O(n log n))
    > when the input length has many small prime factors, and very bad
    > (meaning a naive DFT requiring O(n^2)) when the input size is a prime
    > number.
    """

    # This is one simple way to ensure that the input array
    # has a length with many small prime factors, although it
    # doesn't guarantee that (also hopefully we don't chop too much)
    optimal_input_length = int(numpy.sqrt(len(x))) ** 2
    x = x[:optimal_input_length]
    xp = x - numpy.mean(x)
    f = numpy.fft.fft(xp)
    p = numpy.absolute(numpy.power(f, 2))
    pi = numpy.fft.ifft(p)

    index = int(x.size / 2)
    top = numpy.real(pi)[:index]
    bottom = numpy.sum(numpy.power(xp, 2))
    result = top / bottom


    return result


def find_argmax_after(file, offset):
    return numpy.argmax(file[offset:]) + offset


def autocorrelated_loop(file, search_start, min_loop_width_in_seconds=0.2):
    # Strategy:
    #  1) run an autocorrelation on the file.
    #  3) Find argmax of the autocorrelation
    #  4) define some peak_width and find the next highest peak after current
    #  5) define the loop bounds as from the first peak to the second peak
    #  6) massage the loop bounds using find_similar_sample_index
    #  7) ???
    #  8) Profit!
    autocorrelation = fast_autocorrelate(file)
    return find_loop_from_autocorrelation(
        file,
        autocorrelation,
        search_start,
        min_loop_width_in_seconds
    )


def find_loop_from_autocorrelation(
    file,
    autocorrelation,
    search_start,
    min_loop_width_in_seconds=0.2,
    sample_rate=48000
):
    search_start = int(search_start/2)
    max_autocorrelation_peak_width = int(
        min_loop_width_in_seconds * sample_rate
    )
    loop_start = find_argmax_after(autocorrelation, search_start)
    loop_end = find_argmax_after(
        autocorrelation,
        loop_start + max_autocorrelation_peak_width
    )

    loop_end = find_similar_sample_index(file, loop_start, loop_end) - 1
    return loop_start, (loop_end - loop_start)


def minimize(iterable, callable):
    best_result = None
    best_score = None
    for x in iterable:
        if x:
            score = callable(*x)
            if best_score is None or score < best_score:
                best_score = score
                best_result = x
    return best_result


def autocorrelate_loops(file, sample_rate):
    autocorrelation = fast_autocorrelate(file)
    search_points = [
        3 * len(file) / 4,
        2 * len(file) / 3,
        len(file) / 2,
        len(file) / 3,
    ]
    loop_widths = [0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2, 2.5, 3.]
    for search_point in search_points:
        for width in loop_widths:
            try:
                yield find_loop_from_autocorrelation(
                    file, autocorrelation,
                    search_point, width, sample_rate)
            except ValueError:
                # We couldn't search for a loop width of that size.
                pass
    yield None


def find_loop_points(data, sample_rate):
    channel = data[0]

    result = minimize(
        autocorrelate_loops(channel, sample_rate),
        lambda start, length: abs(channel[start] - channel[start + length])
    )

    if result:
        loop_start, loop_size = result
        return loop_start, loop_start + loop_size


def process(aif, sample_rate=48000):
    file = read_wave_file(aif)

    # loop_start, loop_size = window_match(file)
    # loop_start, loop_size = zero_crossing_match(file)
    loop_start, loop_end = find_loop_points(file)
    loop_size = loop_end - loop_start

    file = file[0]

    print('start, end', loop_start, loop_end)

    plt.plot(file[loop_start:loop_end])
    plt.plot(file[loop_end:loop_start + (2 * loop_size)])
    plt.show()

    plt.plot(file[
        loop_start - (sample_rate * 2):
        loop_start + (sample_rate * 2)
    ])
    plt.axvline(sample_rate * 2)
    plt.axvline((sample_rate * 2) + loop_size)
    plt.show()

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    process(sys.argv[1])
