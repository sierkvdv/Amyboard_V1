# WEERMACHINE v0.4 — resident sketch: WASH + weather display + STORMVANGER.
# New in v0.4:
#  - calmer render rate (FRAME_MS 160) so the serial REPL stays responsive
#  - encoder knob: CLICK = catch 4 beats + fresh chaos pattern,
#    TURN = chaos density (2..12 hits per bar)
#  - auto-catch: first time audio appears after silence, catch automatically
#  - chaos re-rolls itself every 4 bars (evolving, never static)
#  - non-blocking catch (recording runs while rain keeps falling)
#  - status bar shows sample state: [*] sample loaded, [REC] catching
# Recovery: hold BOOT while powering on to skip this sketch.

import random
import struct
import time

import amy
import amyboard
import tulip

VERSION = 'v0.4'
WASH_OSC = 100
LFO_OSC = 101
CHOP_OSCS = (110, 111, 112)
CATCH_PRESET = 1024
TAG_BASE = 300
PPQ = 48
BAR = PPQ * 4

SKY_TOP = 14
SKY_BOT = 110
FRAME_MS = 160  # ~6 fps: plenty for rain, leaves the VM breathing room


def setup_audio():
    amy.send(reset=amy.RESET_SEQUENCER)
    amy.send(sequencer_run=1)  # reset can leave the transport paused
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

try:
    _enc = amyboard.encoder()
    _has_enc = _enc.type is not None and _enc.encoders > 0
except Exception as e:
    print('encoder init failed:', e)
    _enc = None
    _has_enc = False

# ---- state ----
_drops = []
_level = 0.0
_peak_avg = 300.0
_flash = 0
_cooldown = 0
_frame = 0
_errors = 0
_last_render = 0

_used_tags = set()
_have_sample = False
_rec_until = 0        # ticks_ms when a running catch ends (0 = not recording)
_auto_armed = True    # one automatic catch after silence -> audio
_density = 6
_last_reroll_tick = 0
_enc_pos = 0
_btn_down = False


def _input_peak():
    buf = amy.get_input_buffer()
    if not buf:
        return 0
    n = min(128, len(buf) // 2)
    samples = struct.unpack('<%dh' % n, buf[0:n * 2])
    peak = 0
    for i in range(0, n, 2):
        v = samples[i]
        if v < 0:
            v = -v
        if v > peak:
            peak = v
    return peak


# ---- stormvanger (non-blocking) ----
def _clear_tags():
    for t in list(_used_tags):
        amy.send(sequence=',,%d' % t)
    _used_tags.clear()


def _hit(osc, note, vel, tick, period, tag):
    amy.send(osc=osc, wave=amy.PCM_LEFT, preset=CATCH_PRESET,
             note=note, vel=vel, amp={'const': 3.5},
             sequence='%d,%d,%d' % (tick, period, tag))
    _used_tags.add(tag)


def start_catch(beats=4):
    """Begin a non-blocking catch; loop() finishes it when time is up."""
    global _rec_until
    if _rec_until:
        return  # already recording
    seconds = beats * 60.0 / 120.0
    _clear_tags()
    amy.start_sample(preset=CATCH_PRESET, source=amy.SAMPLE_FROM_AUDIO_IN,
                     max_frames=int(44100 * seconds))
    _rec_until = time.ticks_add(time.ticks_ms(), int(seconds * 1000) + 100)


def _finish_catch():
    global _rec_until, _have_sample
    try:
        amy.stop_sample()
    except Exception:
        pass
    amy.send(sequencer_run=1)  # sampling pauses the transport — restart it
    _rec_until = 0
    _have_sample = True
    chaos()


def chaos():
    """(Re)roll a random chop pattern: _density hits/bar, pitched +/-15."""
    if not _have_sample and not _rec_until:
        return
    _clear_tags()
    tag = TAG_BASE
    used = []
    for i in range(_density):
        slot = random.randrange(0, 16)
        while slot in used:
            slot = random.randrange(0, 16)
        used.append(slot)
        note = 60 + random.randrange(0, 31) - 15
        vel = 0.5 + random.randrange(0, 5) / 10.0
        _hit(CHOP_OSCS[i % 3], note, vel, slot * 12, BAR, tag)
        tag += 1


def stilte():
    _clear_tags()
    for osc in CHOP_OSCS:
        amy.send(osc=osc, vel=0)


# ---- drawing ----
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
        jog = max(-x, min(jog, 126 - x))
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
    global _auto_armed, _last_reroll_tick, _enc_pos, _btn_down, _density
    try:
        now = time.ticks_ms()

        # finish a running catch as soon as its window has passed
        if _rec_until and time.ticks_diff(now, _rec_until) >= 0:
            _finish_catch()

        if time.ticks_diff(now, _last_render) < FRAME_MS:
            return
        _last_render = now
        _frame += 1

        peak = _input_peak()
        target = peak / 8000.0
        if target > 1.0:
            target = 1.0
        _level += 0.12 * (target - _level)

        # auto-catch: silence -> audio = grab the first bars automatically
        if _auto_armed and not _rec_until and _level > 0.2:
            _auto_armed = False
            start_catch(4)
        if _level < 0.03 and not _auto_armed and not _rec_until:
            _auto_armed = True  # re-arm during silence for next session

        # encoder: click = new catch, turn = chaos density
        if _has_enc and _frame % 2 == 0:
            try:
                pos = _enc.read(0)
                if pos != _enc_pos:
                    delta = pos - _enc_pos
                    _enc_pos = pos
                    _density = max(2, min(12, _density + delta))
                    if _have_sample:
                        chaos()
                pressed = _enc.button(0)
                if pressed and not _btn_down:
                    start_catch(4)
                _btn_down = pressed
            except Exception:
                pass

        # evolving chaos: re-roll every 4 bars
        if _have_sample and not _rec_until:
            tick = tulip.seq_ticks()
            if tick - _last_reroll_tick >= BAR * 4:
                _last_reroll_tick = tick
                chaos()

        # lightning
        if _cooldown > 0:
            _cooldown -= 1
        if _flash == 0 and _cooldown == 0 and peak > 2600 and peak > 2.6 * _peak_avg:
            _flash = 2
            _cooldown = 12
        _peak_avg += 0.06 * (peak - _peak_avg)

        # rain
        want = 3 + int(_level * 27)
        if len(_drops) < want:
            _spawn_drop()
            if len(_drops) < want - 6:
                _spawn_drop()
        elif len(_drops) > want and _drops:
            _drops.pop(0)

        # ---- draw ----
        sky = 3 if _flash else 0
        _d.fill_rect(0, 0, 128, 128, sky)
        _d.text('WEERMACHINE', 20, 2, 15 if _flash else 6)

        for drop in _drops:
            c = 6 + drop[2]
            _d.fill_rect(drop[0], drop[1], 1, 3 + drop[2] // 2, c)
            drop[1] += drop[2]
            if (_frame + drop[2]) % 3 == 0:
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
        if _rec_until:
            tag_txt = 'REC'
        elif _have_sample:
            tag_txt = '*%d' % _density
        else:
            tag_txt = '--'
        bpm = int(tulip.seq_bpm() + 0.5)
        _d.fill_rect(0, 114, 128, 14, 0)
        _d.text('%-6s %3d %s' % (weather, bpm, tag_txt), 4, 118, 15)

        amyboard.display_refresh()
    except Exception as e:
        _errors += 1
        if _errors <= 3:
            print('loop error:', e)


# initial face + boot marker
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
print('WEERMACHINE', VERSION, 'alive, encoder:', _has_enc)
