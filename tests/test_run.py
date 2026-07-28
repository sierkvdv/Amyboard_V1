# Hypothesis: RESET_SEQUENCER paused the transport; ticks advance but no
# events fire. Fix candidate: sequencer_run=1 restarts the transport.

import time

import amy

amy.send(sequencer_run=1)
print('transport-start verstuurd; blips inplannen...')
amy.send(osc=115, wave=amy.SINE, freq=880, vel=1, sequence='0,96,410')
amy.send(osc=115, vel=0, sequence='12,96,411')
time.sleep(6)
amy.send(sequence=',,410')
amy.send(sequence=',,411')
amy.send(osc=115, vel=0)
print('klaar — hoorde je nu wel piepjes?')
