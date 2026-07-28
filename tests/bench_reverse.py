# Bench for the reverse feature: can we (1) tight-capture the input
# stream in Python, (2) build a reversed mono 22.05 kHz copy, and
# (3) upload it as a second preset — all fast enough to live inside a
# catch? Prints timings for each stage, then plays the result once.

import sys
import time

import amy

print('load_sample_bytes aanwezig:', hasattr(amy, 'load_sample_bytes'))
s = sys.modules['sketch']
print('input level: %.2f' % s._level)

# 1) tight dual-capture: 2 s of input blocks, dedup by content
blocks = []
last = None
polls = 0
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 1000:
    b = amy.get_input_buffer()
    polls += 1
    if b and b != last:
        blocks.append(b)
        last = b
dt = time.ticks_diff(time.ticks_ms(), t0)
print('capture: %d polls, %d unieke blokken in %d ms (vol = ~172)'
      % (polls, len(blocks), dt))

# 2) reversed mono at 22.05 kHz — block by block, never one big buffer
#    (a contiguous 347 KB join MemoryErrors on this heap)
t0 = time.ticks_ms()
out = bytearray(len(blocks) * 128 * 2)  # 128 mono frames per 256-frame block
mv = memoryview(out)
j = 0
for bi in range(len(blocks) - 1, -1, -1):
    src = blocks[bi]
    i = 1020  # last frame's left sample (255 * 4)
    while i >= 0:
        mv[j] = src[i]
        mv[j + 1] = src[i + 1]
        j += 2
        i -= 8  # step back two frames = decimate to 22.05 kHz
print('reverse-build: %d mono-frames in %d ms'
      % (j // 2, time.ticks_diff(time.ticks_ms(), t0)))

# 3) upload as preset 41
t0 = time.ticks_ms()
amy.load_sample_bytes(bytes(mv[0:j]), stereo=False, preset=41,
                      midinote=60, sr=22050)
print('upload: %d bytes in %d ms' % (j, time.ticks_diff(time.ticks_ms(), t0)))

# 4) play it once
amy.send(osc=113, wave=amy.PCM, preset=41, note=60, vel=1,
         amp={'const': 3.0})
print('reverse-sample speelt nu 1x af')
