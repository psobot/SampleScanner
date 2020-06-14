import os
import csv
import sys
import numpy
import itertools
import traceback
from tqdm import tqdm
from tabulate import tabulate

from .wavio import read_wave_file

import matplotlib.pyplot as plt

sampling_rate = 48000.0
assume_stereo_frequency_match = True
CHUNK_SIZE = 2048


def process_all(start, stop, *files):
    start = int(start)
    stop = int(stop)
    chunk_offset = ((-1 * start) % CHUNK_SIZE)
    for file in files:
        stereo = read_wave_file(file)
        left = stereo[0]
        right = stereo[1]
        plt.plot(left[start:stop])
        plt.plot(right[start:stop])
    plt.show()

if __name__ == "__main__":
    process_all(*sys.argv[1:])
