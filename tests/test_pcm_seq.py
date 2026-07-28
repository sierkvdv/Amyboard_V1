# Isolate sequenced-PCM failure with a KNOWN-good event table.
# Blocks: 1) sequenced sine (control), 2) sequenced PCM all-in-one message,
# 3) sequenced PCM + amp dict, 4) WORKAROUND: osc pre-configured directly,
# sequence event only carries note+vel trigger.

import time

import amy

stilte()

print('1) klok-SINE (controle) - 4 s')
amy.send(osc=115, wave=amy.SINE, freq=880, vel=1, sequence='0,96,420')
amy.send(osc=115, vel=0, sequence='12,96,421')
time.sleep(4)
amy.send(sequence=',,420')
amy.send(sequence=',,421')

print('2) klok-PCM alles-in-1 - 5 s')
amy.send(osc=110, wave=amy.PCM_LEFT, preset=1024, note=60, vel=1,
         sequence='0,192,422')
time.sleep(5)
amy.send(sequence=',,422')

print('3) klok-PCM + amp-boost - 5 s')
amy.send(osc=111, wave=amy.PCM_LEFT, preset=1024, note=60, vel=1,
         amp={'const': 3.5}, sequence='0,192,423')
time.sleep(5)
amy.send(sequence=',,423')

print('4) OMWEG: osc vooraf configureren, klok triggert alleen - 5 s')
amy.send(osc=112, wave=amy.PCM_LEFT, preset=1024, amp={'const': 3.5})
amy.send(osc=112, note=60, vel=1, sequence='0,192,424')
time.sleep(5)
amy.send(sequence=',,424')
for o in (110, 111, 112, 115):
    amy.send(osc=o, vel=0)
print('klaar: welke hoorde je? 1-piepjes / 2-flard / 3-flard / 4-flard')
