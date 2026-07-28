# Measure BeatStep Pro CLOCK OUT pulses on CV1 in: sample as fast as
# Python allows for 5 s, count rising edges, estimate pulse interval.

import time

import amyboard

t0 = time.ticks_ms()
n = 0
high = False
peaks = 0
minv = 99.0
maxv = -99.0
edges = []
while time.ticks_diff(time.ticks_ms(), t0) < 5000:
    v = amyboard.cv_in(channel=0)
    n += 1
    if v < minv:
        minv = v
    if v > maxv:
        maxv = v
    if not high and v > 2.0:
        high = True
        peaks += 1
        edges.append(time.ticks_ms())
    elif high and v < 1.0:
        high = False

print('samples: %d (%.0f per sec)' % (n, n / 5.0))
print('spanning: min %.2f V, max %.2f V' % (minv, maxv))
print('pulsen gezien: %d' % peaks)
if len(edges) >= 3:
    iv = [time.ticks_diff(edges[i + 1], edges[i]) for i in range(len(edges) - 1)]
    avg = sum(iv) / len(iv)
    print('gemiddeld interval: %.1f ms' % avg)
    print('  als 1 puls per 16e noot -> %.1f BPM' % (60000.0 / (avg * 4)))
    print('  als 1 puls per 8e noot  -> %.1f BPM' % (60000.0 / (avg * 2)))
    print('  als 1 puls per beat     -> %.1f BPM' % (60000.0 / avg))
