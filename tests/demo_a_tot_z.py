# A-to-Z proof: catch live music -> direct playback x3 -> 8 bars of beats
# fired directly from Python, clock-timed by polling seq_ticks (bypasses the
# broken scheduled-event path entirely; uses only proven ingredients).

import random
import sys
import time

import amy
import tulip

s = sys.modules['sketch']
s.stilte()

print('>>> VANGEN: 2 seconden van je muziek... NU')
amy.start_sample(preset=1024, source=amy.SAMPLE_FROM_AUDIO_IN,
                 max_frames=88200)
time.sleep(2.1)
try:
    amy.stop_sample()
except Exception:
    pass

print('>>> gevangen! Luister: 3x jouw flard, direct afgespeeld')
for note, naam in ((60, 'origineel'), (72, 'octaaf omhoog'),
                   (48, 'octaaf omlaag')):
    print('    ...', naam)
    amy.send(osc=113, wave=amy.PCM_LEFT, preset=1024, note=note, vel=1,
             amp={'const': 3.5})
    time.sleep(2.2)
amy.send(osc=113, vel=0)

print('>>> nu: 8 maten BEATS uit je eigen flard, achtsten op de klok')
notes = (60, 60, 72, 55, 60, 63, 48, 67)
oscs = (110, 111, 112)
start = tulip.seq_ticks()
last_slot = -1
fired = 0
while fired < 64:  # 64 eighths = 8 bars at 4/4
    t = tulip.seq_ticks() - start
    slot = t // 24  # eighth note = 24 ticks at 48 PPQ
    if slot > last_slot:
        last_slot = slot
        n = notes[slot % 8]
        if slot % 8 in (2, 6) and random.randrange(0, 2):
            n += random.randrange(-5, 6)  # loose cannon on the off-hits
        amy.send(osc=oscs[fired % 3], wave=amy.PCM_LEFT, preset=1024,
                 note=n, vel=0.9, amp={'const': 3.5})
        fired += 1
    time.sleep(0.01)

for o in oscs:
    amy.send(osc=o, vel=0)
print('>>> klaar: hoorde je 3 losse flarden en daarna 8 maten beats?')
