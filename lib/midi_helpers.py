import time
import rtmidi


CHANNEL_OFFSET = 0x90 - 1


def all_notes_off(midiout, midi_channel):
    # All notes off
    midiout.send_message([
        (0xB0 - 1) + midi_channel, 0x7B, 0
    ])
    # Reset all controllers
    midiout.send_message([
        (0xB0 - 1) + midi_channel, 0x79, 0
    ])
    time.sleep(1.0)


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
