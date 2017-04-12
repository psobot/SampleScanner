import sys
from wavio import read_wave_file
from constants import bit_depth

default_threshold_samples = (0.001 * float(2 ** (bit_depth - 1)))


def starts_with_click(filename, threshold_samples=default_threshold_samples):
    sample_data = read_wave_file(filename)
    return (abs(sample_data[0][0]) > threshold_samples or
            abs(sample_data[0][1]) > threshold_samples)

if __name__ == "__main__":
    if starts_with_click(sys.argv[1]):
        sys.exit(0)
    else:
        sys.exit(1)
