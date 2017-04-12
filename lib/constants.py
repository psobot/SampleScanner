import numpy

neg80point8db = 0.00009120108393559096
bit_depth = 16
default_silence_threshold = (neg80point8db * (2 ** (bit_depth - 1))) * 4
NUMPY_DTYPE = numpy.int16 if bit_depth == 16 else numpy.int24
SAMPLE_RATE = 48000

EXIT_ON_CLIPPING = True
EXIT_ON_BALANCE_BAD = False  # Doesn't work yet
CLIPPING_CHECK_NOTE = 48  # C4
CLIPPING_THRESHOLD = 0.85
