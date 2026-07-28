# Isolate why sequenced PCM events don't sound while direct ones do.
# Three blocks: A) sequenced sine blips (known-good pattern from earlier),
# B) sequenced PCM bare, C) sequenced PCM with amp boost.
# Also measures the sequencer tick rate machine-side.

import time

import amy
import tulip

stilte()  # from stormvanger.py

t0 = tulip.seq_ticks()
time.sleep(1)
t1 = tulip.seq_ticks()
print('tick-rate: %d ticks/s (verwacht ~96 bij 120 BPM)' % (t1 - t0))

print('A) sine-blips, elke halve maat — 6 s...')
amy.send(osc=115, wave=amy.SINE, freq=880, vel=1, sequence='0,96,400')
amy.send(osc=115, vel=0, sequence='12,96,401')
time.sleep(6)
amy.send(sequence=',,400')
amy.send(sequence=',,401')

print('B) PCM-flard elke maat, kaal — 8 s...')
amy.send(osc=110, wave=amy.PCM_LEFT, preset=1024, note=60, vel=1,
         sequence='0,192,402')
time.sleep(8)
amy.send(sequence=',,402')

print('C) PCM-flard elke maat met amp-boost — 8 s...')
amy.send(osc=110, wave=amy.PCM_LEFT, preset=1024, note=60, vel=1,
         amp={'const': 3.5}, sequence='0,192,403')
time.sleep(8)
amy.send(sequence=',,403')
amy.send(osc=110, vel=0)
print('klaar — wat hoorde je: A-blips? B-flard? C-flard?')
