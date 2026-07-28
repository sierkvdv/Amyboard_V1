# 20-second demo: soft drone + slow pulsing pluck, live waveform on OLED.
# Purpose: let Sierk SEE the display move with the sound.

import time

import amy
import amyboard

amy.reset()
amy.send(tempo=108)

# Drone: two soft low notes
amy.send(synth=1, num_voices=4, patch=5, synth_level=0.5)
amy.send(synth=1, note=40, vel=0.4)
amy.send(synth=1, note=47, vel=0.35)
amy.echo(0.4, 555, 700, 0.5, 0.4)

# A slow repeating pluck so the waveform visibly pulses
amy.send(synth=2, num_voices=2, patch=133, synth_level=0.6)
amy.send(synth=2, note=64, vel=0.7, sequence="0,96,50")
amy.send(synth=2, note=64, vel=0, sequence="24,96,51")

d = amyboard.display
t0 = time.ticks_ms()
frames = 0
while time.ticks_diff(time.ticks_ms(), t0) < 20000:
    amyboard.draw_waveform()
    amyboard.display_refresh()
    frames += 1
    time.sleep(0.05)

print('waveform demo klaar,', frames, 'frames getekend; drone speelt door')
