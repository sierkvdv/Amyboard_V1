# WASH layer test: external audio (DJ mixer / 303 on line in, left channel)
# through AMY as an oscillator: lowpass filter + chorus + tempo echo + reverb.
# Also prints a live input level meter for 40 s so we can SEE signal arrive.

import struct
import time

import amy

WASH_OSC = 100

amy.send(reset=amy.RESET_SEQUENCER)  # kill leftover scheduled events (old demo pluck)
amy.reset()
amy.send(tempo=120)

# Audio-in left channel as oscillator, through a lowpass filter
amy.send(osc=WASH_OSC, wave=amy.AUDIO_IN0, vel=1,
         filter_type=amy.FILTER_LPF, filter_freq=5000, resonance=1.0)

# The weather around it: chorus, tempo-synced echo (dotted 8th @120), reverb
amy.chorus(0.4, 320, 0.4, 0.5)
amy.echo(0.45, 375, 700, 0.45, 0.4)
amy.reverb(0.5, 0.9, 0.5, 3000)


def input_peak():
    buf = amy.get_input_buffer()
    if not buf:
        return 0
    n = len(buf) // 2
    samples = struct.unpack('<%dh' % n, buf)
    peak = 0
    for i in range(0, n, 2):  # left channel = even indices (MicroPython
        v = samples[i]        # tuples don't support step slicing)
        if v < 0:
            v = -v
        if v > peak:
            peak = v
    return peak


t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 40000:
    p = input_peak()
    bar = '#' * min(40, p // 800)
    print('%5d %s' % (p, bar))
    time.sleep(0.3)

print('wash test klaar (wash blijft aan staan)')
