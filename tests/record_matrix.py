# Recording-side trap: catch 2 s of the (short) test tone, then — in
# silence — play the recording back four different ways. Whatever Sierk
# hears (or doesn't) pinpoints the broken link.

import time

import amy

print('wachten tot de toon loopt...')
time.sleep(0.6)
print('OPNEMEN: 2 s...')
amy.start_sample(preset=1024, source=amy.SAMPLE_FROM_AUDIO_IN,
                 max_frames=88200)
time.sleep(2.1)
try:
    amy.stop_sample()
except Exception as e:
    print('stop_sample zei:', e)
amy.send(sequencer_run=1)

print('wachten tot de toon voorbij is...')
time.sleep(3.0)

tests = [
    ('1: PCM-mix, normale toonhoogte', dict(wave=amy.PCM, preset=1024, note=60)),
    ('2: PCM-links, normale toonhoogte', dict(wave=amy.PCM_LEFT, preset=1024, note=60)),
    ('3: PCM-rechts, normale toonhoogte', dict(wave=amy.PCM_RIGHT, preset=1024, note=60)),
    ('4: PCM-mix, octaaf omhoog', dict(wave=amy.PCM, preset=1024, note=72)),
]
for naam, kw in tests:
    print('afspelen', naam)
    amy.send(osc=113, vel=1, amp={'const': 3.0}, **kw)
    time.sleep(2.4)
amy.send(osc=113, vel=0)
print('klaar: welke van de 4 hoorde je?')
