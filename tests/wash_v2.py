# Wash v2: louder, and an actual weather system around the sound.
# - gain x6
# - breathing 24dB lowpass: slow sine LFO sweeps the cutoff ~ +/-0.8 octave
# - wide chorus, quarter-note echo with long feedback tail, big reverb

import amy

amy.send(osc=100, amp={'const': 6.0})

# LFO oscillator (silent, modulation source only)
amy.send(osc=101, wave=amy.SINE, freq=0.13, amp=1)
amy.send(osc=100, mod_source=101,
         filter_type=amy.FILTER_LPF24,
         filter_freq={'const': 2200, 'mod': 0.8},
         resonance=1.8)

amy.send(tempo=120)
amy.chorus(0.6, 320, 0.25, 0.7)
amy.echo(0.5, 500, 1000, 0.6, 0.5)
amy.reverb(0.8, 0.97, 0.4, 3000)

print('wash v2 actief: gain x6, ademend filter, groot weer')
