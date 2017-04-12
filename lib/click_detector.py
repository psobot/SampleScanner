import os
import pdb
import csv
import sys
import time
import numpy
import itertools
import traceback
from tqdm import tqdm
from collections import defaultdict
from tabulate import tabulate
import matplotlib.cm as cm
from spectrogram import plotstft, stft, logscale_spec
from itertools import islice

from wavio import read_wave_file, read_flac_file
from numpy_helpers import sliding_window

import matplotlib.pyplot as plt

sampling_rate = 48000.0
assume_stereo_frequency_match = True
CHUNK_SIZE = 2048

FFT_SIZE = 512
SECOND_DERIVATIVE_THRESHOLD = -15000
ARCTAN_STRETCH_X = 25
PI_OVER_2 = 1.57079


def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, te - ts)
        return result

    return timed


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def find_clicks_using_second_derivatives(*channels):
    #  Not very reliable.
    binsize = 2 ** 10
    samplerate = 48000
    click_bins = set()
    for channel in channels:
        s = stft(channel, binsize)
        sshow, freq = logscale_spec(s, factor=1.0, sr=samplerate)
        ims = 20. * numpy.log10(numpy.abs(sshow) / 10e-6)  # amplitude to db

        second_derivatives = numpy.diff(numpy.sum(ims, axis=1), 2)
        for bin_index, bin in enumerate(
            second_derivatives < SECOND_DERIVATIVE_THRESHOLD
        ):
            if bin:
                click_bins.add((
                    ((bin_index) * binsize / 2),
                    ((bin_index + 1) * binsize / 2)
                ))
    return click_bins


def rolling_window_slow(vertical_similarity):
    window_size = 10
    return [
        (numpy.arctan(float(i) / len(vertical_similarity)
         * ARCTAN_STRETCH_X) / PI_OVER_2)
        * numpy.abs(
            numpy.sum(slice)
        )
        for i, slice in enumerate(
            list(
                window(vertical_similarity, window_size)
            )[:-window_size * 2]
        )
    ]


def rolling_window(vertical_similarity):
    window_size = 10

    to_sum = numpy.array(list(
        vertical_similarity[offset:-(window_size - offset)]
        for offset in xrange(0, window_size)
    ))

    summed = numpy.abs(numpy.sum(to_sum, axis=0))[:-window_size * 2]
    linspace = numpy.linspace(0, ARCTAN_STRETCH_X, len(summed))
    coefficients = numpy.arctan(linspace) / PI_OVER_2

    return summed * coefficients


def find_clicks_old_unreliable(*channels):
    binsize = 2 ** 10
    samplerate = 48000
    click_bins = set()
    for channel in channels:
        s = stft(channel, binsize)
        sshow, freq = logscale_spec(s, factor=1.0, sr=samplerate)
        ims = 20. * numpy.log10(numpy.abs(sshow) / 10e-6)  # amplitude to db

        vertical_similarity = numpy.diff([
            numpy.sqrt(numpy.average((column - numpy.median(column)) ** 2))
            for column in ims
        ])

        threshold = 5
        for bin_index, value in enumerate(rolling_window(vertical_similarity)):
            if value >= threshold:
                click_bins.add((
                    ((bin_index) * binsize / 2),
                    ((bin_index + 1) * binsize / 2)
                ))
    return click_bins


def find_clicks_windowed(*channels):
    binsize = 2 ** 10
    samplerate = 48000
    click_bins = set()
    for channel in channels:
        s = stft(channel, binsize)
        sshow, freq = logscale_spec(s, factor=1.0, sr=samplerate)
        ims = 20. * numpy.log10(numpy.abs(sshow) / 10e-6)  # amplitude to db

        vertical_similarity = numpy.diff([
            numpy.sqrt(numpy.average((column - numpy.median(column)) ** 2))
            for column in ims
        ])

        threshold = 40
        for bin_index, win in enumerate(
            sliding_window(
                rolling_window(vertical_similarity),
                10,
                copy=False,
            )
        ):
            high_point = numpy.max(win)
            avg_baseline = numpy.median(win)
            if (high_point / avg_baseline) > threshold:
                click_bins.add((
                    ((bin_index) * binsize / 2),
                    ((bin_index + 1) * binsize / 2)
                ))
    return click_bins

CLICK_FREQUENCY_CHECKS = [6000, 10666, 13000, 15000, 18619]
CLICK_FREQUENCY_THRESHOLD = 170


def find_clicks_points(*channels):
    binsize = 2 ** 10
    samplerate = 48000

    bins_per_check = defaultdict(set)
    for channel in channels:
        s = stft(channel, binsize)
        sshow, freq = logscale_spec(s, factor=1.0, sr=samplerate)
        ims = 20. * numpy.log10(numpy.abs(sshow) / 10e-6)  # amplitude to db

        for check in CLICK_FREQUENCY_CHECKS:
            check_freq = next(i for i in freq if i > check)
            check_freq_index = freq.index(check_freq)

            check_freq_values = [column[check_freq_index] for column in ims]
            # plt.plot(check_freq_values)
            # plt.show()

            for bin_index, value in enumerate(check_freq_values):
                if value > CLICK_FREQUENCY_THRESHOLD:
                    bins_per_check[check].add((
                        ((bin_index) * binsize / 2),
                        ((bin_index + 1) * binsize / 2)
                    ))

    return set().intersection(*bins_per_check.values())


# 2am: finds clicks by checking a 4-bin window and expects the
# middle 2 bins to be louder for most of their vertical content (?)
# I'm really tired but this seems to work on the test dataset
def find_clicks(*channels):
    binsize = 2 ** 10
    samplerate = 48000

    click_bins = set()
    initial_offset = 2
    for channel in channels:
        s = stft(channel, binsize)
        sshow, freq = logscale_spec(s, factor=1.0, sr=samplerate)
        ims = 20. * numpy.log10(numpy.abs(sshow) / 10e-6)  # amplitude to db

        ims = ims[initial_offset:]

        threshold = 1.01
        freq_count_pct_threshold = 0.095

        win_size = 4
        for bin_index, rows in enumerate(sliding_window(ims, win_size)):
            count_of_matching_freqs = 0

            # todo: make extensible to different window sizes
            middle = (rows[:, 1] + rows[:, 2]) / 2

            middle_over_start = numpy.clip(
                middle / rows[:, 0],
                0,
                threshold
            )
            middle_over_end = numpy.clip(
                middle / rows[:, win_size - 1],
                0,
                threshold
            )

            subtracted = (middle_over_start + middle_over_end) - (
                2 * threshold
            )
            count_of_matching_freqs = len(numpy.where(
                subtracted >= 0
            )[0])
            pct_matching = (count_of_matching_freqs / float(len(freq)))

            if pct_matching < freq_count_pct_threshold:
                click_bins.add((
                    ((bin_index) * binsize / 2),
                    ((bin_index + 1) * binsize / 2)
                ))
    return click_bins


def find_clicks_convolution(*channels):
    binsize = 2 ** 10
    samplerate = 48000

    click_bins = set()
    for channel in channels:
        samples = channel
        s = stft(channel, binsize)
        sshow, freq = logscale_spec(s, factor=1.0, sr=samplerate)
        ims = 20. * numpy.log10(numpy.abs(sshow) / 10e-6)  # amplitude to db

        threshold = 1.01
        freq_count_pct_threshold = 0.20

        convolved = numpy.array(
            [numpy.convolve(c, [0.5, 1, 0.5], 'valid') for c in ims]
        )
        timebins, freqbins = numpy.shape(convolved)
        colormap = "jet"
        plt.figure(figsize=(15, 7.5))
        plt.imshow(numpy.transpose(convolved), origin="lower", aspect="auto", cmap=colormap, interpolation="none")
        plt.colorbar()

        plt.xlabel("time (s)")
        plt.ylabel("frequency (hz)")
        plt.xlim([0, timebins-1])
        plt.ylim([0, freqbins])

        xlocs = numpy.float32(numpy.linspace(0, timebins-1, 5))
        plt.xticks(xlocs, ["%.02f" % l for l in ((xlocs*len(samples)/timebins)+(0.5*binsize))/samplerate])
        ylocs = numpy.int16(numpy.round(numpy.linspace(0, freqbins-1, 10)))
        plt.yticks(ylocs, ["%.02f" % freq[i] for i in ylocs])
        plt.show()

        # for bin_index, columns in enumerate(sliding_window(ims, 3)):
        #     count_of_matching_freqs = 0
        #     for i in xrange(0, len(columns)):
        #         middle_over_start = columns[i][1] / columns[i][0]
        #         middle_over_end = columns[i][1] / columns[i][2]
        #         if middle_over_start > threshold and \
        #                 middle_over_end > threshold:
        #             count_of_matching_freqs += 1
        #     if count_of_matching_freqs / float(len(freq)) \
        #             > freq_count_pct_threshold:
        #         click_bins.add((
        #             ((bin_index) * binsize / 2),
        #             ((bin_index + 1) * binsize / 2)
        #         ))

    return click_bins


def process_all(start, stop, *files):
    start = int(start)
    stop = int(stop)
    total_results = defaultdict(set)
    for file in tqdm(files, desc='Detecting clicks...'):
        found_clicks = set()
        if file.endswith('flac'):
            stereo = read_flac_file(file)
        else:
            stereo = read_wave_file(file)
        left = stereo[0]
        right = stereo[1]
        for bin_start, bin_end in find_clicks(
            left[start:stop],
            right[start:stop]
        ):
            found_clicks.add((bin_start, bin_end))
        if found_clicks:
            total_results[file] = found_clicks
    for file, clicks in total_results.iteritems():
        print file, 'has', len(clicks), 'clicks at', clicks
    if not total_results:
        print "No clicks found in", \
            files[0], "or", len(files) - 1, 'other files.'
    return total_results
    # print "To delete, run: "
    # for file in total_results.keys():
    #     print "rm \"%s\"" % file


def show_all(save, start, stop, *files):
    start = int(start)
    stop = int(stop)

    binsize = 2 ** 10
    samplerate = 48000
    total_results = defaultdict(set)
    for file in tqdm(files, desc='Detecting clicks...'):
        found_clicks = set()
        if file.endswith('flac'):
            stereo = read_flac_file(file)
        else:
            stereo = read_wave_file(file)
        left = stereo[0][start:stop]
        right = stereo[1][start:stop]

        for channel in (right,):
            s = stft(channel, binsize)
            samples = channel
            colormap = "jet"
            sshow, freq = logscale_spec(s, factor=1.0, sr=samplerate)
            ims = 20. * numpy.log10(numpy.abs(sshow) / 10e-6)  # amplitude to db

            timebins, freqbins = numpy.shape(ims)

            plt.figure(figsize=(15, 7.5))
            plt.imshow(numpy.transpose(ims), origin="lower", aspect="auto", cmap=colormap, interpolation="none")
            plt.colorbar()

            plt.xlabel("time (s)")
            plt.ylabel("frequency (hz)")
            plt.xlim([0, timebins-1])
            plt.ylim([0, freqbins])

            xlocs = numpy.float32(numpy.linspace(0, timebins-1, 5))
            plt.xticks(xlocs, ["%.02f" % l for l in ((xlocs*len(samples)/timebins)+(0.5*binsize))/samplerate])
            ylocs = numpy.int16(numpy.round(numpy.linspace(0, freqbins-1, 10)))
            plt.yticks(ylocs, ["%.02f" % freq[i] for i in ylocs])

            for bin_start, bin_end in find_clicks(channel):
                if not save:
                    plt.axvline(bin_start / (2 ** 10))
                found_clicks.add((bin_start, bin_end))

            if found_clicks:
                total_results[file] = found_clicks
        if save:
            plotstft(samplerate, left, plotpath=file + '.png')
            plt.close('all')
        else:
            plt.show()
    for file, clicks in total_results.iteritems():
        print file, 'has', len(clicks), 'clicks at', clicks
    if not total_results:
        print "No clicks found in", \
            files[0], "or", len(files) - 1, 'other files.'
    return total_results


if __name__ == "__main__":
    if sys.argv[1] == 'show':
        sys.exit(1 if show_all(False, *sys.argv[2:]) else 0)
    if sys.argv[1] == 'save':
        sys.exit(1 if show_all(True, *sys.argv[2:]) else 0)
    else:
        sys.exit(1 if process_all(*sys.argv[1:]) else 0)
