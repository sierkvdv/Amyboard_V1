# Controlled sample pipeline test. Run while the PC test tone is playing:
# catches 1 s of the tone, then plays it back 3 times: normal pitch,
# octave up, octave down. Sierk reports which (if any) he hears.

import time

import amy

stilte()  # clear any running chop patterns (defined by stormvanger.py)

print('1) vangen: 1 seconde van de testtoon...')
catch(2)  # 2 beats @ 120 BPM = 1.0 s -> preset 1024

time.sleep(0.5)
print('2) afspelen NORMAAL (note 60)')
amy.send(osc=110, wave=amy.PCM_LEFT, preset=1024, note=60, vel=1)
time.sleep(2.5)

print('3) afspelen OCTAAF OMHOOG (note 72)')
amy.send(osc=110, wave=amy.PCM_LEFT, preset=1024, note=72, vel=1)
time.sleep(2.5)

print('4) afspelen OCTAAF OMLAAG (note 48)')
amy.send(osc=110, wave=amy.PCM_LEFT, preset=1024, note=48, vel=1)
time.sleep(3)

print('5) zelfde maar met wave=PCM (mix) als vergelijking')
amy.send(osc=110, wave=amy.PCM, preset=1024, note=60, vel=1)
time.sleep(2.5)

amy.send(osc=110, vel=0)
print('test klaar — wat hoorde je? (4 flarden? welke wel/niet?)')
