# Quick 15 s input meter (no reset — leaves the wash setup untouched).
import struct
import time

import amy

# Re-assert the wash path (harmless if already set)
amy.send(osc=100, wave=amy.AUDIO_IN0, vel=1,
         filter_type=amy.FILTER_LPF, filter_freq=5000, resonance=1.0)


def input_peak():
    buf = amy.get_input_buffer()
    if not buf:
        return 0
    n = len(buf) // 2
    samples = struct.unpack('<%dh' % n, buf)
    peak = 0
    for i in range(0, n, 2):
        v = samples[i]
        if v < 0:
            v = -v
        if v > peak:
            peak = v
    return peak


t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 15000:
    p = input_peak()
    print('%5d %s' % (p, '#' * min(50, p // 500)))
    time.sleep(0.4)
print('meter klaar')
