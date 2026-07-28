# M1 clock-lock monitor — Weermachine (working title)
# Registers MIDI + sequencer callbacks and enables external clock follow.
# Everything stays registered after this script ends (mpremote resume keeps
# the board namespace alive), so later exec calls can read live status:
#   m1_status()  -> prints BPM estimate, tick count, transport, recent MIDI

import time
import amy
import tulip
import midi

m1_events = []            # (ts_ms, bytes) of recent incoming MIDI messages
m1_beats = []             # (ts_ms, tick) once per quarter note (period=48)
m1_transport = {'last': None}

def m1_on_midi(msg):
    # Callback runs via the MicroPython scheduler: keep it tiny, no prints.
    b = bytes(msg)
    if b == b'\xfa':
        m1_transport['last'] = 'START'
    elif b == b'\xfc':
        m1_transport['last'] = 'STOP'
    m1_events.append((time.ticks_ms(), b))
    if len(m1_events) > 200:
        m1_events.pop(0)

def m1_on_beat(tick):
    m1_beats.append((time.ticks_ms(), tick))
    if len(m1_beats) > 64:
        m1_beats.pop(0)

def m1_bpm():
    # Average over the last few quarter notes; None while no clock flows.
    if len(m1_beats) < 2:
        return None
    recent = m1_beats[-9:]
    span = time.ticks_diff(recent[-1][0], recent[0][0])
    if span <= 0:
        return None
    return 60000.0 * (len(recent) - 1) / span

def m1_status():
    bpm = m1_bpm()
    print('--- M1 status ---')
    print('BPM:', ('%.1f' % bpm) if bpm else 'geen clock',
          '| tick:', tulip.seq_ticks(),
          '| transport:', m1_transport['last'],
          '| beats seen:', len(m1_beats))
    print('midi events:', len(m1_events), '- laatste:')
    for ts, b in m1_events[-12:]:
        print('  ', ' '.join('%02X' % x for x in b))

midi.add_callback(m1_on_midi)
m1_slot = tulip.seq_add_callback(m1_on_beat, 0, 48)
tulip.external_midi_sync(True)
print('M1 monitor armed: follow mode ON, seq slot', m1_slot)
