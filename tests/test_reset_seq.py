# Discriminating test: is the sequencer event table clogged (fix: full
# reset clears it -> scheduled blips sound) or does RESET_SEQUENCER itself
# poison scheduling (-> still silent)?

import time

import amy

print('1) directe controle-piep (880 Hz, moet je altijd horen)')
amy.send(osc=115, wave=amy.SINE, freq=880, vel=1)
time.sleep(0.4)
amy.send(osc=115, vel=0)
time.sleep(1)

print('2) volledige sequencer-reset + transport start + blips (1320 Hz)')
amy.send(reset=amy.RESET_SEQUENCER)
time.sleep(0.2)
amy.send(sequencer_run=1)
amy.send(osc=115, wave=amy.SINE, freq=1320, vel=1, sequence='0,96,1')
amy.send(osc=115, vel=0, sequence='12,96,2')
time.sleep(5)
amy.send(sequence=',,1')
amy.send(sequence=',,2')
amy.send(osc=115, vel=0)
print('klaar: hoorde je (1) de lage losse piep en (2) de hoge herhaal-piepjes?')
