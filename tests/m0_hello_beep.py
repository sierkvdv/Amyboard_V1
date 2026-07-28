# M0 "hello beep" — Weermachine (working title)
# AMYboard (ESP32-S3, MicroPython + AMY synth engine)
# Run live over the REPL via mpremote; no need to persist as sketch.py yet.

import os
import amy

print("=" * 40)
print("M0 hello beep")
print("board:   ", os.uname().machine)
print("firmware:", os.uname().version)
print("=" * 40)

amy.reset()  # clean slate: all oscillators off

# One-second 440 Hz sine beep. Note-on now, note-off scheduled 1000 ms
# later; both sends return immediately and the AMY engine fires the
# note-off by itself (documented time= future scheduling).
start = amy.millis()
amy.send(osc=0, wave=amy.SINE, freq=440, vel=1, time=start)
amy.send(osc=0, vel=0, time=start + 1000)

print("M0: 440 Hz beep on line out, stops after 1 s")
