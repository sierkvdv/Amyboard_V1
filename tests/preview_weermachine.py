# First-breath preview — drone + tempo-locked arp on the internal clock.
# No MIDI involved; everything is scheduled by AMY's own 48-PPQ sequencer.

import amy

amy.reset()
amy.send(tempo=125)  # match where Sierk left the BeatStep knob :)

# --- Drone layer: soft Juno pad, two held notes (C2 + G2) ---------------
amy.send(synth=1, num_voices=3, patch=3, synth_level=0.4)
amy.send(synth=1, note=36, vel=0.5)
amy.send(synth=1, note=43, vel=0.4)

# --- Tempo-synced echo: dotted eighth at 125 BPM = 360 ms ---------------
amy.echo(0.5, 360, 500, 0.45, 0.3)

# --- Pluck arp: C-minor pentatonic figure over 2 beats (96 ticks) -------
amy.send(synth=2, num_voices=2, patch=133, synth_level=0.5)
PERIOD = 96
STEPS = [(0, 60), (24, 63), (48, 67), (84, 70)]
tag = 10
for tick, note in STEPS:
    amy.send(synth=2, note=note, vel=0.6, sequence="%d,%d,%d" % (tick, PERIOD, tag))
    off_tick = (tick + 18) % PERIOD
    amy.send(synth=2, note=note, vel=0, sequence="%d,%d,%d" % (off_tick, PERIOD, tag + 1))
    tag += 2

print("Weermachine preview: drone + arp, interne clock, 125 BPM")
