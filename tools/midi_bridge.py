# midi_bridge.py — desktop-side USB MIDI bridge (plan B for missing TRS cable)
# Forwards every MIDI message from the BeatStep Pro's USB port to the
# AMYboard's USB MIDI gadget port. On the board, USB MIDI feeds the exact
# same parser/callbacks/clock-sync as the TRS MIDI in jack, so M1 works
# identically. Prints a per-type message count every 5 seconds.

import time

import mido


def find_port(names, needle):
    for name in names:
        if needle.lower() in name.lower():
            return name
    return None


src = find_port(mido.get_input_names(), 'beatstep')
dst = find_port(mido.get_output_names(), 'amyboard')
if not src or not dst:
    raise SystemExit(f'port missing: src={src} dst={dst}')
print(f'bridge: [{src}] -> [{dst}]', flush=True)

# Only forward what the board needs; drop polytouch/aftertouch floods and
# sysex — the board's USB MIDI gadget input has been seen to wedge under
# high message load (observed 2026-07-27 with pad-pressure streams).
FORWARD_TYPES = {
    'clock', 'start', 'stop', 'continue',
    'note_on', 'note_off', 'control_change', 'program_change', 'pitchwheel',
}

counts = {}
dropped = {}
last_report = time.time()
with mido.open_input(src) as midi_in, mido.open_output(dst) as midi_out:
    for msg in midi_in:
        if msg.type in FORWARD_TYPES:
            midi_out.send(msg)
            counts[msg.type] = counts.get(msg.type, 0) + 1
        else:
            dropped[msg.type] = dropped.get(msg.type, 0) + 1
        now = time.time()
        if now - last_report >= 5:
            print('fwd:', counts, '| dropped:', dropped, flush=True)
            last_report = now
