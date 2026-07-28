# WEERMACHINE v0.3 — resident sketch: WASH audio + live weather display.
# The OLED shows weather driven by the line-in audio level: rain density
# follows loudness, lightning strikes on sharp transients, status bar shows
# conditions + BPM. Audio: line-in (left) -> breathing 24dB LPF -> chorus +
# quarter-note echo + big reverb.
# Recovery: hold BOOT while powering on to skip this sketch.

import random
import struct
import time

import amy
import amyboard
import tulip

VERSION = 'v0.3'
WASH_OSC = 100
LFO_OSC = 101

SKY_TOP = 14
SKY_BOT = 110
FRAME_MS = 70  # min ms between rendered frames, whatever the loop cadence


def setup_audio():
    amy.send(reset=amy.RESET_SEQUENCER)
    amy.reset()
    amy.send(tempo=120)
    amy.send(osc=WASH_OSC, wave=amy.AUDIO_IN0, vel=1, amp={'const': 6.0})
    amy.send(osc=LFO_OSC, wave=amy.SINE, freq=0.05, amp=1)
    amy.send(osc=WASH_OSC, mod_source=LFO_OSC,
             filter_type=amy.FILTER_LPF24,
             filter_freq={'const': 2600, 'mod': 0.35},
             resonance=1.2)
    amy.chorus(0.6, 320, 0.25, 0.7)
    amy.echo(0.5, 500, 1000, 0.6, 0.5)
    amy.reverb(0.8, 0.97, 0.4, 3000)


try:
    setup_audio()
except Exception as e:
    print('audio setup failed:', e)

try:
    amyboard.init_display()
except Exception as e:
    print('display init failed:', e)
_d = amyboard.display

_drops = []        # each drop: [x, y, speed]
_level = 0.0       # smoothed loudness 0..1
_peak_avg = 300.0  # running average of raw peaks, for transient detection
_flash = 0         # lightning frames remaining
_cooldown = 0
_frame = 0
_errors = 0
_last_render = 0


def _input_peak():
    buf = amy.get_input_buffer()
    if not buf:
        return 0
    n = min(128, len(buf) // 2)
    samples = struct.unpack('<%dh' % n, buf[0:n * 2])
    peak = 0
    for i in range(0, n, 2):  # left channel = even indices
        v = samples[i]
        if v < 0:
            v = -v
        if v > peak:
            peak = v
    return peak


def _spawn_drop():
    _drops.append([random.randrange(2, 126),
                   SKY_TOP + random.randrange(0, 20),
                   3 + random.randrange(0, 5)])


def _draw_bolt():
    x = random.randrange(30, 98)
    y = SKY_TOP + 2
    while y < 80:
        seg = 8 + random.randrange(0, 8)
        _d.fill_rect(x, y, 2, seg, 15)
        y += seg
        jog = random.randrange(0, 17) - 8
        jog = max(-x, min(jog, 126 - x))  # keep every jog segment on-screen
        if jog < 0:
            _d.fill_rect(x + jog, y - 2, -jog, 2, 15)
        elif jog > 0:
            _d.fill_rect(x, y - 2, jog + 2, 2, 15)
        x = x + jog
        if x < 4:
            x = 4
        if x > 122:
            x = 122


def loop(*args):
    global _level, _peak_avg, _flash, _cooldown, _frame, _errors, _last_render
    try:
        now = time.ticks_ms()
        if time.ticks_diff(now, _last_render) < FRAME_MS:
            return
        _last_render = now
        _frame += 1

        peak = _input_peak()

        # smooth loudness (a raw peak of ~8000 counts as "loud")
        target = peak / 8000.0
        if target > 1.0:
            target = 1.0
        _level += 0.12 * (target - _level)

        # transient detection -> lightning
        if _cooldown > 0:
            _cooldown -= 1
        if _flash == 0 and _cooldown == 0 and peak > 2600 and peak > 2.6 * _peak_avg:
            _flash = 2
            _cooldown = 12
        _peak_avg += 0.06 * (peak - _peak_avg)

        # rain population follows loudness
        want = 3 + int(_level * 27)
        if len(_drops) < want:
            _spawn_drop()
            if len(_drops) < want - 6:
                _spawn_drop()
        elif len(_drops) > want and _drops:
            _drops.pop(0)

        # ---- draw the frame ----
        sky = 3 if _flash else 0
        _d.fill_rect(0, 0, 128, 128, sky)
        _d.text('WEERMACHINE', 20, 2, 15 if _flash else 6)

        for drop in _drops:
            c = 6 + drop[2]  # faster drops draw brighter (9..13)
            _d.fill_rect(drop[0], drop[1], 1, 3 + drop[2] // 2, c)
            drop[1] += drop[2]
            if (_frame + drop[2]) % 3 == 0:  # a little wind drift
                drop[0] += 1
            if drop[1] > SKY_BOT or drop[0] > 126:
                drop[0] = random.randrange(2, 126)
                drop[1] = SKY_TOP
                drop[2] = 3 + random.randrange(0, 5)

        if _flash:
            _draw_bolt()
            _flash -= 1

        # status bar
        if _level < 0.06:
            weather = 'calm'
        elif _level < 0.25:
            weather = 'breeze'
        elif _level < 0.6:
            weather = 'rain'
        else:
            weather = 'STORM'
        bpm = int(tulip.seq_bpm() + 0.5)
        _d.fill_rect(0, 114, 128, 14, 0)
        _d.text('%-6s %3d BPM' % (weather, bpm), 4, 118, 15)

        amyboard.display_refresh()
    except Exception as e:
        _errors += 1
        if _errors <= 3:
            print('loop error:', e)


# initial face + boot marker (wrapped: a faceless boot must not kill audio)
try:
    _d.fill_rect(0, 0, 128, 128, 0)
    _d.text('WEERMACHINE', 20, 2, 10)
    _d.text(VERSION, 50, 60, 8)
    amyboard.display_refresh()
except Exception as e:
    print('boot face failed:', e)
try:
    with open('/user/current/weermachine_boot.txt', 'w') as f:
        f.write(VERSION)
except Exception:
    pass
print('WEERMACHINE', VERSION, 'alive')
