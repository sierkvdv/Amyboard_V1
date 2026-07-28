# Weermachine

Tempo-locked soundscape instrument built on an [AMYboard](https://amyboard.com)
(ESP32-S3 + AMY synth engine, MicroPython). It takes live audio in, wraps it in
weather, catches fragments of it into memory, and forges new beats from them —
following the tempo of an Arturia BeatStep Pro. The OLED shows the result as a
rainstorm that reacts to the sound.

Comments and identifiers are English; the patch card and session notes are Dutch
(the instrument's owner is).

## What it does right now (sketch v0.12)

| Layer | Behaviour |
|---|---|
| **Wash** | Line-in audio runs through AMY as an oscillator: breathing 24 dB lowpass (0.05 Hz LFO), chorus, tempo-synced echo, big reverb. |
| **Stormvanger** (catcher) | Records ~2 s of line-in into sample RAM — plus a reversed 22.05 kHz copy of the last second — then fires pitched chops on eighth-note boundaries. Pitch palette follows the notes you played (melody buffer), widens with density, and every hit gets ±15 cent micro-drift. Keeps playing when the input stops. |
| **Reverse ghosts** | In the middle knob zone (density 5–8) ~35% of hits play the reversed copy. Outside that zone everything plays forward. |
| **MIDI in (TRS)** | BeatStep play/stop = transport (play re-anchors the downbeat). Every incoming note on any channel fires the caught sample at that pitch immediately, velocity-sensitive, even while paused (solo mode). A white flash strip confirms receipt. MIDI clock (F8) drives the sequencer ticks in lock-step. |
| **Weather display** | Rain density follows input loudness; lightning strikes on transients; status bar shows condition, tempo and catch state. |
| **Clock follow** | Reads BeatStep Pro CLOCK OUT pulses on CV1 in and steers the sequencer tempo (`CLK` on screen). Falls back to 120 BPM after 2.5 s of silence. |
| **CV outputs** | CV2 out = 5 V gate square on quarter notes at the followed tempo. CV1 out = slow weather LFO for filter modulation. |
| **Encoder** | Click steps a 4-item menu: `STORM` (density 0–12: 0 = machine layer off, middle = reverse zone, high = dense chaos) · `ECHO` (0–10, 0 = dry) · `GALM` (reverb 0–10, 0 = dry) · `ADEM` (filter-breathing depth 0–10, 0 = still). Turn sets the value of the current item. Keep turning left past the bottom for a moment (`REC? <<<` on screen) = fresh catch. |

Architecture note: everything runs from a `_thread` background heartbeat (30 ms)
that `micropython.schedule()`s the service routine; the factory `loop()` hook is
deliberately a no-op because it starves as soon as external MIDI clock flows in.

## Patch overview

```
PC / mixer / 303  ──(mono)──►  R2 line in      (audio: wash + catch material)
AMYboard R2 line out ─────────►  headphones / mixer
BeatStep CLOCK OUT ──(mono)──►  R4 CV1 in      (tempo follow)
R4 CV1 out ──────────────────►  filter CV in   (weather LFO)     [free to patch]
R5 CV2 out ──────────────────►  gate in        (quarter notes)   [free to patch]
BeatStep MIDI OUT ─(stereo)──►  R3 MIDI in     [PENDING — needs a TRS cable]
USB-C ───────────────────────►  computer       (power + REPL)
```

Front panel rows, counting from the USB-C end: `1 S/PDIF · 2 line · 3 MIDI ·
4 CV1 · 5 CV2`; left column = inputs, right column = outputs.

**DIP switches** (back of board, all four together): OFF = line level (current
setting), ON = 10 Vpp modular. 1 & 2 affect the input, 3 & 4 the output — never
boost the output with headphones plugged in.

A printable panel card with all of this lives in [`patchkaart.html`](patchkaart.html).

## Working on it

The board appears as a serial port (COM5 on the author's machine) and runs
`sketch.py` from `/user/current/` at boot.

```bash
python -m mpremote resume connect COM5 exec "print('hi')"          # talk to it
python -m mpremote resume connect COM5 run tests/test_playback.py   # run a script
python -m mpremote resume connect COM5 fs cp sketch.py :/user/current/sketch.py
python -m mpremote resume connect COM5 exec "import machine; machine.reset()"
```

Always pass `resume` — without it mpremote soft-resets and the serial connection
dies. Live state of the running sketch is readable from the REPL, which is the
fastest way to debug it:

```python
import sys; s = sys.modules['sketch']
print(s._level, s._have_sample, s._ext_bpm, s._errors)
```

If a sketch ever misbehaves, hold **BOOT** while powering on to skip it (that
also runs the hardware self-test). **RST** is a plain restart.

## Firmware gotchas found the hard way

These cost a full day of debugging; they are not in the official docs.

- **`start_sample(preset=...)` needs a LOW preset number.** The docs suggest user
  samples live at 1024+; on firmware `2026-07-26` recording into 1024 silently
  produces nothing. Presets 30 and 40 work.
- **Play recorded samples with `wave=amy.PCM`.** `PCM_LEFT` was never audible on
  a recorded preset, only on the factory drum presets.
- **Don't schedule PCM chops with `sequence=`.** Scheduled events proved
  unreliable after sampling; the beat engine instead polls `tulip.seq_ticks()`
  in `loop()` and sends hits directly.
- **Never mass-delete sequencer tags that don't exist** (`sequence=',,N'` in a
  loop) — it clogs the event table and new events stop firing. Track real tags, or
  recover with `reset=RESET_SEQUENCER` followed by `sequencer_run=1`.
- **USB MIDI gadget input wedges** after a few minutes of continuous traffic
  (clock + notes) and needs a reboot. TRS MIDI in is the reliable path.
- **CLOCK OUT pulses ring:** the BeatStep's analogue clock pulse produces
  spurious edges, so the follower debounces at 70 ms and takes the smallest
  plausible interval as the true 16th-note period.
- The CV-in ADC is an **ADS1015 (12-bit)**, not the ADS1115 the product page
  implies, and saturates near **+5.65 V** on USB power alone.

## Layout

```
sketch.py          resident program — copy to /user/current/sketch.py
stormvanger.py     standalone catcher (REPL-driven; superseded by sketch.py)
patchkaart.html    printable panel card / manual (Dutch)
calibration.json   CV loopback measurements, 2026-07-27
PATCHNOTES.md      session-by-session build log (Dutch)
tests/             milestone and debugging scripts, roughly chronological
tools/             desktop-side helpers (USB MIDI bridge)
archive/           earlier sketch versions + the factory sketch backup
```

## Where it's going

Next: a dedicated TRS cable for the MIDI in (the headphone cable works but
wants its life back) · the Juno/DX7 drone layer in the same key · scenes on
pads · moving the board to the rack alongside a Behringer 2600 (gate threshold
4 V, so the 5 V gates drive it directly) · upstream bug reports to Shore Pine.
