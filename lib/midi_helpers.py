import time
import rtmidi


CHANNEL_OFFSET = 0x90 - 1
CC_CHANNEL_OFFSET = 0xB0 - 1


def all_notes_off(midiout, midi_channel):
    # All notes off
    midiout.send_message([
        CC_CHANNEL_OFFSET + midi_channel, 0x7B, 0
    ])
    # Reset all controllers
    midiout.send_message([
        CC_CHANNEL_OFFSET + midi_channel, 0x79, 0
    ])


def open_midi_port(midi_port_name):
    midiout = rtmidi.MidiOut()
    for i, port_name in enumerate(midiout.get_ports()):
        if not midi_port_name or midi_port_name.lower() in port_name.lower():
            midiout.open_port(i)
            return midiout
    else:
        raise Exception("Could not find port matching %s in ports %s!" % (
            midi_port_name, midiout.get_ports()
        ))


def set_program_number(midiout, midi_channel, program_number):
    if program_number is not None:
        print "Sending program change to program %d..." % program_number
        # Bank change (fine) to (program_number / 128)
        midiout.send_message([
            CC_CHANNEL_OFFSET + midi_channel,
            0x20,
            int(program_number / 128),
        ])
        # Program change to program number % 128
        midiout.send_message([
            CHANNEL_OFFSET + midi_channel,
            0xC0,
            program_number % 128,
        ])

    # All notes off, but like, a lot
    for _ in xrange(0, 2):
        all_notes_off(midiout, midi_channel)

    time.sleep(0.5)
