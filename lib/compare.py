import os
import csv
import sys
import numpy
import itertools
import traceback
from tqdm import tqdm
from tabulate import tabulate

from .utils import normalized, trim_mono_data
from .audio_helpers import fundamental_frequency
from .wavio import read_wave_file

import matplotlib.pyplot as plt

sampling_rate = 44100.0
assume_stereo_frequency_match = True


def aligned_sublists(*lists):
    min_peak_index = min([numpy.argmax(list) for list in lists])
    return [list[(numpy.argmax(list) - min_peak_index):] for list in lists]


def peak_diff(lista, listb):
    return float(numpy.amax(lista)) / float(numpy.amax(listb))


def normalized_difference(lista, listb):
    lista = trim_mono_data(normalized(lista))
    listb = trim_mono_data(normalized(listb))

    compare = min(len(lista), len(listb))
    return numpy.sum(
        numpy.absolute(
            lista[:compare] - listb[:compare]
        )
    ) / compare


def freq_diff(lista, listb, only_compare_first=100000):
    return fundamental_frequency(lista[:only_compare_first]) /\
        fundamental_frequency(listb[:only_compare_first])


def shift_freq(list, factor):
    num_output_points = int(float(len(list)) / factor)
    output_x_points = numpy.linspace(0, len(list), num_output_points)
    input_x_points = numpy.linspace(0, len(list), len(list))

    return numpy.interp(
        output_x_points,
        input_x_points,
        list,
    )


def generate_diffs(filea, fileb):
    wavea = read_wave_file(filea, True)
    waveb = read_wave_file(fileb, True)

    diffl = normalized_difference(*aligned_sublists(wavea[0], waveb[0]))
    diffr = normalized_difference(*aligned_sublists(wavea[1], waveb[1]))

    peakl = peak_diff(wavea[0], waveb[0])
    peakr = peak_diff(wavea[1], waveb[1])

    # for line in aligned_sublists(wavea[0], waveb[0]):
    #     plt.plot(normalized(line[:10000]))
    # plt.show()

    # louder_a = wavea[0] if numpy.amax(wavea[0]) \
    #   > numpy.amax(wavea[1]) else wavea[1]
    # louder_b = waveb[0] if numpy.amax(waveb[0]) \
    #   > numpy.amax(waveb[1]) else waveb[1]

    # freqd = freq_diff(normalized(louder_a), normalized(louder_b))

    return (
        diffl, diffr,
        peakl, peakr,
        0,  # freqd,
        os.path.split(filea)[-1], os.path.split(fileb)[-1]
    )


def generate_pairs(infiles):
    for filea, fileb in tqdm(list(itertools.combinations(infiles, 2))):
        yield generate_diffs(filea, fileb)


def process_all(aifs):
    results = []
    try:
        for result in generate_pairs(aifs):
            results.append(result)
    except KeyboardInterrupt as e:
        traceback.print_exc(e)
        pass

    headers = (
        '% diff L', '% diff R',
        'x peak L', 'x peak R',
        'x freq',
        'file a', 'file b'
    )
    results = sorted(
        results,
        key=lambda dl_dr_pl_pr_freqd_fa_fb: dl_dr_pl_pr_freqd_fa_fb[0] + dl_dr_pl_pr_freqd_fa_fb[1] + abs(dl_dr_pl_pr_freqd_fa_fb[4] - 1))
    with open('results.csv', 'wb') as f:
        writer = csv.writer(f)
        writer.writerows([headers])
        writer.writerows(results)

    print("%d results" % len(results))
    print(tabulate(
        results,
        headers=headers,
        floatfmt='.4f'
    ))


def graph_ffts():
    files = ['A1_v111_15.00s.aif', 'A2_v31_15.00s.aif']
    for file in files:
        stereo = read_wave_file(os.path.join(root_dir, file))
        left = stereo[0]
        right = stereo[1]
        list = left[:100000]

        w = numpy.fft.rfft(list)
        freqs = numpy.fft.fftfreq(len(w))

        # Find the peak in the coefficients
        # idx = numpy.argmax(numpy.abs(w[:len(w) / 2]))
        idx = numpy.argmax(numpy.abs(w))
        freq = freqs[idx]
        plt.plot(w)
        print(freq)
        print(fundamental_frequency(normalized(list)), \
            fundamental_frequency(normalized(left + right)))
    # plt.show()


def freq_shift():
    files = ['A1_v111_15.00s.aif', 'A1_v95_15.00s.aif']
    wavea, waveb = [
        read_wave_file(os.path.join(root_dir, file)) for file in files
    ]

    louder_a = wavea[0] if (numpy.amax(wavea[0]) >
                            numpy.amax(wavea[1])) else wavea[1]
    louder_b = waveb[0] if (numpy.amax(waveb[0]) >
                            numpy.amax(waveb[1])) else waveb[1]

    freqd = freq_diff(normalized(louder_a), normalized(louder_b))

    waveb_shifted = [shift_freq(channel, freqd) for channel in waveb]
    louder_shifted_b = waveb_shifted[0] if (numpy.amax(waveb_shifted[0]) >
                                            numpy.amax(waveb_shifted[1])) \
        else waveb_shifted[1]

    shifted_freqd = freq_diff(
        normalized(louder_a),
        normalized(louder_shifted_b)
    )

    # lefts_aligned = aligned_sublists(wavea[0], waveb[0])
    rights_aligned = aligned_sublists(wavea[1], waveb[1])
    # shifted_lefts_aligned = aligned_sublists(wavea[0], waveb_shifted[0])

    diffl = normalized_difference(*aligned_sublists(wavea[0], waveb[0]))
    diffr = normalized_difference(*aligned_sublists(wavea[1], waveb[1]))

    plt.plot(normalized(rights_aligned[0][:10000]))
    plt.plot(normalized(rights_aligned[1][:10000]))
    plt.plot(numpy.absolute(
        normalized(rights_aligned[0][:10000]) -
        normalized(rights_aligned[1][:10000])
    ))
    plt.show()

    shifted_diffl = normalized_difference(*aligned_sublists(wavea[0],
                                                            waveb_shifted[0]))
    shifted_diffr = normalized_difference(*aligned_sublists(wavea[1],
                                                            waveb_shifted[1]))

    print(files)
    print('diffs\t\t', diffl, diffr)
    print('shifted diffs\t', shifted_diffl, shifted_diffr)
    print('freqs', freqd)
    print('shifted freqs', shifted_freqd)


if __name__ == "__main__":
    process_all(sys.argv[1:])
