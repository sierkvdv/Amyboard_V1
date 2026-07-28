# After a fresh boot, watch the sequencer ticks and the sketch frame
# counter evolve while the BeatStep MIDI stream flows in. Shows WHEN the
# freeze happens and WHAT freezes (ticks, loop, or both).

import sys
import time

import tulip

s = sys.modules['sketch']
for i in range(6):
    t0 = tulip.seq_ticks()
    f0 = s._frame
    time.sleep(2)
    print('meting %d: ticks +%d | frames +%d | midi-noten totaal %d'
          % (i, tulip.seq_ticks() - t0, s._frame - f0, s._midi_notes))
print('klaar')
