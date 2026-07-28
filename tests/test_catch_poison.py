# Catch-poison test: does start_sample/stop_sample pause the sequencer
# transport, and does sequencer_run=1 revive it?

import time

import amy

stilte()
print('vangst uitvoeren (1 s)...')
catch(2)

print('A) blips inplannen ZONDER herstel — 3 s (verwacht: stil)')
amy.send(osc=115, wave=amy.SINE, freq=880, vel=1, sequence='0,96,430')
amy.send(osc=115, vel=0, sequence='12,96,431')
time.sleep(3)

print('B) transport-herstart — 4 s (nu zouden de piepjes moeten starten)')
amy.send(sequencer_run=1)
time.sleep(4)

amy.send(sequence=',,430')
amy.send(sequence=',,431')
amy.send(osc=115, vel=0)
print('klaar: kwamen de piepjes pas in fase B?')
