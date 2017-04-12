# SampleScanner

![SampleScanner Logo](https://cloud.githubusercontent.com/assets/213293/24964018/1dcb4092-1f6e-11e7-8b3b-47704e6c8aeb.png)


SampleScanner is a command-line tool to turn MIDI instruments (usually hardware) into virtual (software) instruments automatically. It's similar to [Redmatica's now-discontinued _AutoSampler_](http://www.soundonsound.com/reviews/redmatica-autosampler) software (now part of Apple's [MainStage](https://441k.com/sampling-synths-with-auto-sampler-in-mainstage-3-412deb8f900e)), but open-source and cross-platform.

## Features

 - Uses native system integration (via `rtmidi` and `pyAudio`) for compatibility with all audio and MIDI devices
 - Outputs to the open-source [sfz 2.0 sample format](http://ariaengine.com/overview/sfz-format/), playable by [Sforzando](https://www.plogue.com/products/sforzando/) (and others)
 - Optional FLAC compression (on by default) to reduce sample set file size by up to 75%
 - Flexible configuration options and extensive command-line interface
 - Expermimental looping algorithm to extend perpetual samples
 - Clipping detection at sample time
 - 100% Python to enable cross-platform compatibility (only tested on macOS at the moment)

## Installation

Requires a working `python`, `pip`, and `ffmpeg` to be installed on the system.

```
git clone git@github.com:psobot/SampleScanner
cd SampleScanner
pip install -r requirements.txt
```

## How to run

Run `./samplescanner -h` for a full argument listing:

```contentsof<samplescanner -h>
usage: samplescanner [-h] [--program-number PROGRAM_NUMBER]
                     [--low-key LOW_KEY] [--high-key HIGH_KEY]
                     [--velocity-levels VELOCITY_LEVELS [VELOCITY_LEVELS ...]]
                     [--key-skip KEY_RANGE] [--max-attempts MAX_ATTEMPTS]
                     [--limit LIMIT] [--has-portamento] [--sample-asc]
                     [--no-flac] [--no-delete] [--loop] [--ignore-clicks]
                     [--midi-port-name MIDI_PORT_NAME]
                     [--midi-channel MIDI_CHANNEL]
                     [--audio-interface-name AUDIO_INTERFACE_NAME]
                     [--sample-rate SAMPLE_RATE] [--print-progress]
                     output_folder

create SFZ files from external audio devices

optional arguments:
  -h, --help            show this help message and exit

Sampling Options:
  --program-number PROGRAM_NUMBER
                        switch to a program number before recording
  --low-key LOW_KEY     key to start sampling from (key name, octave number)
  --high-key HIGH_KEY   key to stop sampling at (key name, octave number)
  --velocity-levels VELOCITY_LEVELS [VELOCITY_LEVELS ...]
                        velocity levels (in [1, 127]) to sample
  --key-skip KEY_RANGE  number of keys covered by one sample
  --max-attempts MAX_ATTEMPTS
                        maximum number of tries to resample a note
  --limit LIMIT         length in seconds of longest sample
  --has-portamento      play each note once before sampling to avoid
                        portamento sweeps between notes
  --sample-asc          sample notes from low to high (default false)

Output Options:
  output_folder         name of output folder
  --no-flac             don't compress output to flac samples
  --no-delete           leave temporary .aif files in place after flac
                        compression
  --loop                attempt to loop sounds (should only be used with
                        sounds with infinite sustain)
  --ignore-clicks       turn off click/audio corruption checks (default false)

MIDI/Audio IO Options:
  --midi-port-name MIDI_PORT_NAME
                        name of MIDI device to use
  --midi-channel MIDI_CHANNEL
                        MIDI channel to send messages on
  --audio-interface-name AUDIO_INTERFACE_NAME
                        name of audio input device to use
  --sample-rate SAMPLE_RATE
                        sample rate to use. audio interface must support this
                        rate.

Misc Options:
  --print-progress      show text-based VU meters in terminal (default false,
                        can cause audio artifacts)
```

## Copyright and License

tl;dr: SampleScanner is &copy; 2015-2017 [Peter Sobot](https://petersobot.com), and released under the MIT License.

```contentsof<cat LICENSE>
The MIT License

Copyright (c) 2015-2017 Peter Sobot https://petersobot.com github@petersobot.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
