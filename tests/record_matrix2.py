# Double recording trap:
#  B) record LINE-IN (PC test tone) into preset 40  (low preset number!)
#  A) record AMY's OWN OUTPUT (a sine we play ourselves) into preset 30
# Then play both back in silence. What Sierk hears splits the fault:
#  - both audible  -> preset 1024 was an invalid slot (docs vs firmware)
#  - only A        -> recording works, AUDIO_IN source is broken
#  - neither       -> start_sample itself is broken on this build

import time

import amy

SAMPLE_FROM_OUTPUT = 0  # from amy source: start_sample default source

print('B) line-in opnemen naar preset 40 (testtoon loopt)...')
time.sleep(0.6)
amy.start_sample(preset=40, source=amy.SAMPLE_FROM_AUDIO_IN,
                 max_frames=88200, midinote=60)
time.sleep(2.1)
try:
    amy.stop_sample()
except Exception as e:
    print('stop_sample B:', e)

print('A) eigen synth-toon opnemen naar preset 30...')
amy.send(osc=114, wave=amy.SINE, freq=330, vel=0.8)
time.sleep(0.3)
amy.start_sample(preset=30, source=SAMPLE_FROM_OUTPUT,
                 max_frames=66150, midinote=60)
time.sleep(1.6)
try:
    amy.stop_sample()
except Exception as e:
    print('stop_sample A:', e)
amy.send(osc=114, vel=0)
amy.send(sequencer_run=1)

print('stilte-pauze...')
time.sleep(3.0)

print('AFSPELEN 1: de line-in-opname (preset 40)')
amy.send(osc=113, wave=amy.PCM, preset=40, note=60, vel=1, amp={'const': 3.0})
time.sleep(2.6)

print('AFSPELEN 2: de synth-opname (preset 30)')
amy.send(osc=113, wave=amy.PCM, preset=30, note=60, vel=1, amp={'const': 3.0})
time.sleep(2.6)

amy.send(osc=113, vel=0)
print('klaar: hoorde je 1 (toon-opname), 2 (synth-opname), beide of geen?')
