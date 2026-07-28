# Patch tour: play 20 Juno patches for ~3.5 s each, with the patch number
# large on the OLED and the live waveform dancing below it. Sierk listens
# and calls out the numbers he likes.

import time

import amy
import amyboard

CANDIDATES = [0, 3, 5, 7, 10, 13, 17, 18, 21, 26, 33, 41, 44, 49, 57, 63, 74, 89, 101, 117]

amy.reset()
amy.send(synth=1, num_voices=4, patch=CANDIDATES[0], synth_level=0.6)
amy.echo(0.35, 555, 700, 0.5, 0.4)
d = amyboard.display

for p in CANDIDATES:
    amy.send(synth=1, patch=p)          # hot-swap keeps the voice count
    amy.send(synth=1, note=40, vel=0.4)
    amy.send(synth=1, note=47, vel=0.35)
    amy.send(synth=1, note=52, vel=0.3)
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < 3500:
        amyboard.draw_waveform()
        d.fill_rect(0, 0, 128, 26, 0)   # keep the patch number on top
        d.text('PATCH  %d' % p, 20, 8, 15)
        amyboard.display_refresh()
        time.sleep(0.08)
    amy.send(synth=1, vel=0)            # all notes off on this synth

print('proefrit klaar')
