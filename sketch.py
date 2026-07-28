# WEERMACHINE v0.15 — resident sketch: WASH + weather display + STORMVANGER.
# New in v0.15:
#  - TONEN menu item: the beats wander in pitch per bar — 0 sticks to
#    your melody, 10 jumps wildly (up to +/- an octave)
#  - big menu box on screen (name + value + position dots): clicking
#    through the menu is unmissable now
#  - ADEM is audible: breathing gets FASTER as well as deeper
# v0.14: hit length follows STORM (calm = short ticks, 9+ = full ring)
# v0.13:
#  - knob feedback on screen while turning: a position bar (ghost zone
#    marked, '<' at the left = keep going to re-record) plus a weather
#    icon per menu item — the STORM sun spins and dims as you open up,
#    spins BACKWARDS inside the reverse zone (5..8)
# v0.12: encoder CLICK steps a 4-item menu (STORM/ECHO/GALM/ADEM),
#    TURN sets the value, turning left past the bottom = fresh catch.
# Recovery: hold BOOT while powering on to skip this sketch.

import random
import struct
import time

import _thread
import gc
import amy
import amyboard
import micropython
import midi
import tulip

VERSION = 'v0.15'
WASH_OSC = 100
LFO_OSC = 101
CHOP_OSCS = (110, 111, 112)
CATCH_PRESET = 40  # LOW preset slot! 1024 (per docs) is an invalid
                   # recording slot on fw 2026-07-26 — records vanish.
REV_PRESET = 41    # Python-built reversed copy (1 s, mono 22.05 kHz)
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

# weather LFO on CV1 out is set up after audio (reset would wipe it)
# NOTE: called below, after its definition — see end of file.

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
_have_reverse = False
_rev_bytes = None     # reversed copy waiting for upload after the catch
_rec_until = 0        # ticks_ms when a running catch ends (0 = not recording)
_auto_armed = True    # one automatic catch after silence -> audio
_density = 6
_last_reroll_tick = 0
_enc_pos = 0
_btn_down = False

# ---- encoder menu (v0.12): click steps items, turn sets the value ----
MENU_ITEMS = ('STORM', 'TONEN', 'ECHO', 'GALM', 'ADEM')
_menu = 0             # index into MENU_ITEMS; STORM = the density knob
_menu_flash = 0       # ticks_ms deadline: show "ITEM value" in status bar
_tone_lvl = 3         # 0..10 pitch wander: per-bar transpose of the beats
_bar_shift = 0        # current bar's transpose, rolled by the beat engine
_echo_lvl = 5         # 0..10 -> amy.echo level 0.0..1.0 (0 = dry)
_verb_lvl = 8         # 0..10 -> amy.reverb level 0.0..1.0 (0 = dry)
_breath = 4           # 0..10 -> filter LFO: deeper AND faster breathing
_rewind = 0           # extra left-steps past the bottom (re-record gesture)
_rewind_t = 0
_enc_accum = 0        # raw detents; 2 raw detents = 1 value step (half speed)


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


# ---- stormvanger (loop-driven beat engine) ----
# No sequence-scheduling: hits fire directly from loop() on eighth-note
# boundaries read from seq_ticks. Every ingredient here is ear-proven:
# wave=PCM (mix), low preset slot, direct sends.
_pattern = []      # list of (slot 0..7, note, vel)
_last_slot = -1
_osc_rot = 0
_bar_count = 0
_cuts = []         # (osc, deadline_ms): timed note-offs that keep machine
                   # hits short at low density (the effects do the fading)

# ---- external clock follow (BeatStep Pro CLOCK OUT -> CV1 in) ----
# Assumes 1 pulse per 16th note (BSP default). We burst-sample the CV
# input briefly on every loop pass; missed pulses give interval multiples,
# so the estimator takes the MINIMUM plausible interval in the window.
_cv_high = False
_edge_times = []
_ext_bpm = 0.0
_ext_last_edge = 0
_ext_last_apply = 0
_ext_active = False

# ---- CV outputs: gates on the beat + weather LFO ----
GATE_CV_CH = 1     # CV2 out jack: 5V gate square, quarter notes, 50% duty
LFO_SYNTH = 5      # synth rendered straight onto CV1 out (weather LFO)
_gate_state = False
_lfo_ok = False

# ---- MIDI in (BeatStep over TRS): transport + melody following ----
# NOTE: we deliberately do NOT use external_midi_sync — it freezes the whole
# sketch when the clock stops (verified 2026-07-28). Tempo comes from the CV
# pulse follower; MIDI provides start/stop and the pitches for the chops.
_running = True        # transport: follows BeatStep play/stop once seen
_transport_evt = 0     # 1 = start received, 2 = stop received (set in cb)
_melody = []           # last note-ons from the BeatStep (ring of 8)
_fire = []             # incoming notes to fire as immediate sample hits
_hit_flash = 0         # frames of on-screen feedback per live hit
_midi_notes = 0        # counters, readable over the REPL for verification
_midi_transport = 0


def _on_midi(m):
    """MIDI-in callback: keep it tiny — flags and counters only, all real
    work happens in loop()."""
    global _transport_evt, _midi_notes, _midi_transport
    try:
        b = bytes(m)
        if b == b'\xfa':
            _transport_evt = 1
            _midi_transport += 1
        elif b == b'\xfc':
            _transport_evt = 2
            _midi_transport += 1
        elif len(b) == 3 and (b[0] & 0xF0) == 0x90 and b[2] > 0:
            _melody.append(b[1])
            if len(_melody) > 8:
                _melody.pop(0)
            if len(_fire) < 8:
                _fire.append((b[1], b[2]))  # play it NOW (also while paused)
            _midi_notes += 1
    except Exception:
        pass


def start_catch(beats=4):
    """Begin a catch. The C engine records the clean forward sample; we
    tight-capture 1 s in Python alongside it for the reversed copy
    (blocks the service ~1.5 s — the screen shows REC, that's fine)."""
    global _rec_until, _rev_bytes
    if _rec_until:
        return  # already recording
    seconds = beats * 60.0 / 120.0
    stilte()  # hush the beat engine while we record
    gc.collect()
    amy.start_sample(preset=CATCH_PRESET, source=amy.SAMPLE_FROM_AUDIO_IN,
                     max_frames=int(44100 * seconds))
    _rec_until = time.ticks_add(time.ticks_ms(), int(seconds * 1000) + 100)
    try:  # show REC right away, since we're about to block a bit
        _d.fill_rect(0, 114, 128, 14, 0)
        _d.text('REC', 4, 118, 15)
        amyboard.display_refresh()
    except Exception:
        pass
    try:
        blocks = []
        last = None
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < 1000:
            b = amy.get_input_buffer()
            if b and b != last:
                blocks.append(b)
                last = b
        # build reversed mono 22.05 kHz, block-wise (heap is too small
        # for one big join — learned via MemoryError)
        out = bytearray(len(blocks) * 256)
        mv = memoryview(out)
        j = 0
        for bi in range(len(blocks) - 1, -1, -1):
            src = blocks[bi]
            i = 1020
            while i >= 0:
                mv[j] = src[i]
                mv[j + 1] = src[i + 1]
                j += 2
                i -= 8
        _rev_bytes = bytes(mv[0:j])
    except Exception as e:
        print('reverse capture failed:', e)
        _rev_bytes = None


def _finish_catch():
    global _rec_until, _have_sample, _have_reverse, _rev_bytes
    try:
        amy.stop_sample()
    except Exception:
        pass
    if _rev_bytes:
        try:
            amy.load_sample_bytes(_rev_bytes, stereo=False, preset=REV_PRESET,
                                  midinote=60, sr=22050)
            _have_reverse = True
        except Exception as e:
            print('reverse upload failed:', e)
            _have_reverse = False
        _rev_bytes = None
        gc.collect()
    _rec_until = 0
    _have_sample = True
    chaos()


def chaos():
    """(Re)roll the pattern: _density hits over 8 eighth-note slots.
    Pitches follow the BeatStep melody when we have one (with octave
    jumps for drama); otherwise random +/-15 semitones around 60.
    Density 0 = machine layer off (knob fully left)."""
    global _pattern
    if _density <= 0:
        _pattern = []
        return
    # the knob shapes character, not just count: further right = wider
    # intervals and more octave jumps around the played melody
    intervals = (0, 0, 5, -5, 7, -7, 3, -3)[:2 + _density // 2]
    oct_chance = 1 + _density // 3  # out of 10
    spread = 4 + _density
    # the middle of the knob (5..8) is the ghost zone: some hits play
    # the reversed copy; outside it, everything runs forward
    rev_zone = _have_reverse and 5 <= _density <= 8
    pat = []
    for i in range(_density):
        slot = random.randrange(0, 8)
        if _melody:
            note = random.choice(_melody) + random.choice(intervals)
            if random.randrange(0, 10) < oct_chance:
                note += random.choice((-12, 12))
        else:
            note = 60 + random.randrange(0, 2 * spread + 1) - spread
        vel = 0.55 + random.randrange(0, 5) / 10.0
        rev = rev_zone and random.randrange(0, 100) < 35
        pat.append((slot, note, vel, rev))
    _pattern = pat


def setup_weather_lfo():
    """Route a slow sine synth straight onto CV1 out (weather LFO).
    Experimental: uses documented set_cv_out(synth) audio->CV routing."""
    global _lfo_ok
    try:
        amy.send(synth=LFO_SYNTH, num_voices=1, oscs_per_voice=1)
        amy.send(synth=LFO_SYNTH, osc=0, wave=amy.SINE, freq=0.1,
                 amp={'const': 1.0})
        amy.send(synth=LFO_SYNTH, note=60, vel=1)
        amyboard.set_cv_out(channel=0, synth=LFO_SYNTH)
        _lfo_ok = True
    except Exception as e:
        print('weather LFO setup failed:', e)


def _gate_tick(slot):
    """5V gate square on CV2 out: high on even slots (quarter-note rate,
    50% duty). Runs whether or not a sample is loaded — the pulse follows
    whatever tempo the machine is on (Arturia-follow included)."""
    global _gate_state
    want_high = (slot % 2) == 0
    if want_high != _gate_state:
        _gate_state = want_high
        try:
            amyboard.cv_out(5.0 if want_high else 0.0, channel=GATE_CV_CH)
        except Exception:
            pass


def _clock_follow():
    """Burst-sample CV1 for ~12 ms, detect rising edges, estimate BPM from
    the smallest plausible edge interval, and steer the sequencer tempo."""
    global _cv_high, _ext_bpm, _ext_last_edge, _ext_last_apply, _ext_active
    t_end = time.ticks_add(time.ticks_ms(), 12)
    while time.ticks_diff(t_end, time.ticks_ms()) > 0:
        v = amyboard.cv_in(channel=0)
        now = time.ticks_ms()
        if not _cv_high and v > 1.8:
            _cv_high = True
            # debounce: ignore ringing re-triggers within 70 ms (16ths at
            # 200 BPM are 75 ms apart, so real pulses always pass)
            if not _edge_times or time.ticks_diff(now, _edge_times[-1]) > 70:
                _edge_times.append(now)
                if len(_edge_times) > 9:
                    _edge_times.pop(0)
                _ext_last_edge = now
        elif _cv_high and v < 1.0:
            _cv_high = False
    now = time.ticks_ms()
    if _ext_last_edge and time.ticks_diff(now, _ext_last_edge) > 2500:
        # clock gone: fall back to internal 120 once
        if _ext_active:
            _ext_active = False
            _ext_bpm = 0.0
            del _edge_times[:]
            amy.send(tempo=120)
        return
    if len(_edge_times) < 3:
        return
    best = 100000
    for i in range(len(_edge_times) - 1):
        iv = time.ticks_diff(_edge_times[i + 1], _edge_times[i])
        if 40 < iv < 1500 and iv < best:
            best = iv
    if best == 100000:
        return
    bpm = 60000.0 / (best * 4)  # 1 pulse per 16th
    if bpm < 55 or bpm > 220:
        return
    if _ext_bpm:
        _ext_bpm += 0.15 * (bpm - _ext_bpm)  # heavy smoothing: calm display
    else:
        _ext_bpm = bpm
    _ext_active = True
    if time.ticks_diff(now, _ext_last_apply) > 500:
        _ext_last_apply = now
        amy.send(tempo=_ext_bpm)


def _beat_engine():
    """Called every loop() pass (ungated): fire pattern hits on eighth
    boundaries derived from the sequencer tick clock."""
    global _last_slot, _osc_rot, _bar_count
    if not _running or not _have_sample or _rec_until or not _pattern:
        return
    slot = (tulip.seq_ticks() // 24) % 8  # eighth note = 24 ticks @ 48 PPQ
    if slot == _last_slot:
        return
    global _bar_shift
    _last_slot = slot
    if slot == 0:
        _bar_count += 1
        # further right = the pattern refreshes faster (4/2/1 bars)
        rb = 4 if _density <= 4 else (2 if _density <= 8 else 1)
        if _bar_count % rb == 0:
            chaos()
        # TONEN: every bar the whole pattern wanders in pitch — palette
        # widens with the knob (0 = stay put, 10 = up to an octave away)
        pal = ((0,), (0, 0, 2, -2), (0, 2, -2, 5, -5),
               (0, 3, -3, 5, -5, 7, -7), (0, 4, -4, 7, -7, 12, -12))
        _bar_shift = random.choice(pal[min(4, (_tone_lvl + 2) // 3)])
    global _cuts
    for sl, note, vel, rev in _pattern:
        if sl == slot:
            n = note + _bar_shift
            if _density >= 5 and random.randrange(0, 8) == 0:
                n += random.choice((-7, -5, 5, 7))  # stray gust
            n += random.randrange(-15, 16) / 100.0  # weather micro-drift
            _osc_rot += 1
            osc = CHOP_OSCS[_osc_rot % 3]
            amy.send(osc=osc, wave=amy.PCM,
                     preset=REV_PRESET if rev else CATCH_PRESET,
                     note=n, vel=vel, amp={'const': 3.5})
            if _density <= 8:
                # calm = a short tick, the echo/reverb do the fading;
                # further open = longer fragments; 9+ rings out in full
                _cuts = [c for c in _cuts if c[0] != osc]
                _cuts.append((osc, time.ticks_add(
                    time.ticks_ms(), 80 + _density * 45)))


def stilte():
    global _pattern, _cuts
    _pattern = []
    _cuts = []
    for osc in CHOP_OSCS:
        amy.send(osc=osc, vel=0)


def _apply_fx(item):
    """Re-send one effect with its current menu value. Uses the exact same
    calls as setup_audio(), only the level changes — 0 means dry/still.
    (TONEN needs no call here: the beat engine reads it directly.)"""
    try:
        if item == 2:
            amy.echo(_echo_lvl / 10.0, 500, 1000, 0.6, 0.5)
        elif item == 3:
            amy.reverb(_verb_lvl / 10.0, 0.97, 0.4, 3000)
        elif item == 4:
            # audible breathing: deeper AND faster as you open up
            amy.send(osc=LFO_OSC, freq=0.05 + _breath * 0.03)
            amy.send(osc=WASH_OSC,
                     filter_freq={'const': 2600, 'mod': _breath / 8.0})
    except Exception as e:
        print('fx apply failed:', e)


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


# 16 points on a radius-10 circle (22.5 deg steps), integers only —
# no float math per frame, and no math-module dependency
_CIRC = ((10, 0), (9, 4), (7, 7), (4, 9), (0, 10), (-4, 9), (-7, 7),
         (-9, 4), (-10, 0), (-9, -4), (-7, -7), (-4, -9), (0, -10),
         (4, -9), (7, -7), (9, -4))


def _draw_knob():
    """Knob feedback while the menu flash is live: a big menu box (name,
    value, position dots — clicking through must be unmissable), a
    position bar with the ghost zone marked ('<' at the left = keep
    turning to re-record), and a weather icon per item."""
    if _menu == 0:
        val, vmax = _density, 12
    elif _menu == 1:
        val, vmax = _tone_lvl, 10
    elif _menu == 2:
        val, vmax = _echo_lvl, 10
    elif _menu == 3:
        val, vmax = _verb_lvl, 10
    else:
        val, vmax = _breath, 10
    # the menu box
    _d.fill_rect(20, 16, 88, 36, 1)
    _d.hline(20, 16, 88, 13)
    _d.hline(20, 51, 88, 13)
    _d.vline(20, 16, 36, 13)
    _d.vline(107, 16, 36, 13)
    _d.text(MENU_ITEMS[_menu], 28, 22, 15)
    _d.text('-' if (_menu == 0 and val <= 0) else str(val), 88, 22, 11)
    for i in range(len(MENU_ITEMS)):
        x = 30 + i * 14
        if i == _menu:
            _d.fill_rect(x, 42, 8, 4, 15)
        else:
            _d.fill_rect(x + 2, 43, 3, 2, 6)
    # the position bar
    x0, w, by = 14, 100, 90
    _d.fill_rect(x0, by + 5, w, 2, 6)          # the rail
    _d.text('<', 2, by, 7)                     # past the left edge = REC
    if _menu == 0:
        _d.fill_rect(x0 + w * 5 // 12, by + 2, w * 3 // 12, 8, 4)  # 5..8
    px = x0 + w * val // vmax
    _d.fill_rect(px - 1, by - 1, 4, 13, 15)    # cursor
    # the icon, between box and bar
    cx, cy = 64, 71
    if _menu == 0:
        # the sun: fewer rays + dimmer + smaller as the storm grows
        bright = 15 - val
        if bright < 3:
            bright = 3
        rays = 8 - val // 2
        core = 4 if val < 7 else 3
        _d.fill_rect(cx - core, cy - core, core * 2, core * 2, bright)
        rev = 5 <= val <= 8
        base = (-_frame if rev else _frame) * (2 if val >= 9 else 1)
        for i in range(rays):
            dx, dy = _CIRC[(base + i * 16 // rays) % 16]
            _d.fill_rect(cx + dx - 1, cy + dy - 1, 2, 2, bright)
        if rev:
            _d.text('<<', cx - 34, cy - 4, 11)
            _d.text('<<', cx + 18, cy - 4, 11)
    elif _menu == 1:
        # wandering tones: three notes hopping, hop height = value
        for i in range(3):
            ph = (_frame * (i + 2) // 2 + i * 5) % 12
            tri = ph if ph < 6 else 12 - ph    # integer triangle wave
            dy = tri * val // 7
            x = cx - 22 + i * 17
            _d.fill_rect(x, cy + 4 - dy, 5, 4, 14 - i * 3)
            _d.vline(x + 5, cy - 3 - dy, 7, 14 - i * 3)
        if val == 0:
            _d.text('vast', cx + 14, cy - 4, 8)
    elif _menu == 2:
        # echo taps: repeating squares, shrinking and fading
        b = 15
        ex = cx - 26
        for i in range(1 + min(4, val // 2)):
            s = 9 - i
            _d.fill_rect(ex, cy - s // 2, s, s, b)
            ex += s + 5
            if b > 6:
                b -= 3
        if val == 0:
            _d.text('dry', cx + 10, cy - 4, 8)
    elif _menu == 3:
        # reverb: expanding rings around a core
        _d.fill_rect(cx - 2, cy - 2, 4, 4, 13)
        for i in range(min(4, (val + 2) // 3)):
            r = 4 + i * 4
            c = 11 - i * 2
            _d.hline(cx - r, cy - r, r * 2, c)
            _d.hline(cx - r, cy + r, r * 2, c)
            _d.vline(cx - r, cy - r, r * 2, c)
            _d.vline(cx + r, cy - r, r * 2 + 1, c)
        if val == 0:
            _d.text('dry', cx + 10, cy - 4, 8)
    else:
        # breathing filter: a square that inhales/exhales, depth = value
        ph = _frame % 12
        tri = ph if ph < 6 else 12 - ph        # integer triangle wave 0..6
        s = 3 + tri * val // 8
        _d.hline(cx - s, cy - s, s * 2, 12)
        _d.hline(cx - s, cy + s, s * 2, 12)
        _d.vline(cx - s, cy - s, s * 2, 12)
        _d.vline(cx + s, cy - s, s * 2 + 1, 12)


def loop(*args):
    # Deliberately empty. The factory loop() starves whenever external MIDI
    # clock flows in (verified 2026-07-28: F8 stream -> zero loop calls), so
    # the machine runs on its own hardware timer instead — see _service().
    pass


def _service(_arg):
    global _level, _peak_avg, _flash, _cooldown, _frame, _errors, _last_render
    global _auto_armed, _last_reroll_tick, _enc_pos, _btn_down, _density
    global _running, _transport_evt, _svc_pending, _osc_rot, _hit_flash
    global _menu, _menu_flash, _tone_lvl, _echo_lvl, _verb_lvl, _breath
    global _rewind, _rewind_t, _enc_accum, _cuts
    _svc_pending = False
    try:
        # live fire: every incoming note plays the caught sample at that
        # pitch immediately — transport state irrelevant (solo on pause!)
        while _fire:
            n, v = _fire.pop(0)
            _hit_flash = 2  # always show reception, even before a catch
            if _have_sample and not _rec_until:
                _osc_rot += 1
                osc = CHOP_OSCS[_osc_rot % 3]
                _cuts = [c for c in _cuts if c[0] != osc]  # pads ring full
                amy.send(osc=osc, wave=amy.PCM,
                         preset=CATCH_PRESET, note=n,
                         vel=0.4 + 0.6 * v / 127.0, amp={'const': 3.5})
        now = time.ticks_ms()

        # timed note-offs: keep machine hits short at low STORM values
        if _cuts:
            left = []
            for o, t in _cuts:
                if time.ticks_diff(now, t) >= 0:
                    amy.send(osc=o, vel=0)
                else:
                    left.append((o, t))
            _cuts = left

        # finish a running catch as soon as its window has passed
        if _rec_until and time.ticks_diff(now, _rec_until) >= 0:
            _finish_catch()

        # transport events from the BeatStep (set by the MIDI callback)
        if _transport_evt:
            evt = _transport_evt
            _transport_evt = 0
            if evt == 1:
                _running = True
                try:
                    amy.send(reset=amy.RESET_TIMEBASE)  # downbeat = his press
                except Exception:
                    pass
                chaos()  # fresh pattern on every start
            else:
                _running = False
                for osc in CHOP_OSCS:
                    amy.send(osc=osc, vel=0)
                _gate_tick(1)  # force gate low

        # clock-follow + gates + beat engine run on EVERY call
        _clock_follow()
        if _running:
            _gate_tick((tulip.seq_ticks() // 24) % 8)
        _beat_engine()

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

        # encoder: click = next menu item, turn = value of that item,
        # keep turning left past the bottom = fresh catch (re-record)
        if _has_enc and _frame % 2 == 0:
            try:
                pos = _enc.read(0)
                delta = 0
                if pos != _enc_pos:
                    # half speed: 2 raw detents = 1 step (remainder kept,
                    # so nothing is lost between passes)
                    _enc_accum += pos - _enc_pos
                    _enc_pos = pos
                    _menu_flash = time.ticks_add(now, 2000)
                    if _enc_accum >= 2:
                        delta = _enc_accum // 2
                    elif _enc_accum <= -2:
                        delta = -((-_enc_accum) // 2)
                    _enc_accum -= delta * 2
                if delta:
                    if _menu == 0:
                        at_min = _density <= 0
                        _density = max(0, min(12, _density + delta))
                        if _have_sample:
                            chaos()
                            if _density <= 0:
                                for osc in CHOP_OSCS:
                                    amy.send(osc=osc, vel=0)
                    elif _menu == 1:
                        at_min = _tone_lvl <= 0
                        _tone_lvl = max(0, min(10, _tone_lvl + delta))
                    elif _menu == 2:
                        at_min = _echo_lvl <= 0
                        _echo_lvl = max(0, min(10, _echo_lvl + delta))
                        _apply_fx(2)
                    elif _menu == 3:
                        at_min = _verb_lvl <= 0
                        _verb_lvl = max(0, min(10, _verb_lvl + delta))
                        _apply_fx(3)
                    else:
                        at_min = _breath <= 0
                        _breath = max(0, min(10, _breath + delta))
                        _apply_fx(4)
                    # re-record: extra left-detents while already at the
                    # bottom accumulate; enough of them within ~1.5 s = REC
                    if delta < 0 and at_min:
                        if time.ticks_diff(now, _rewind_t) > 1500:
                            _rewind = 0
                        _rewind += -delta
                        _rewind_t = now
                        # 4 half-speed steps = ~8 raw detents of turning
                        if _rewind >= 4:
                            _rewind = 0
                            start_catch(4)
                    else:
                        _rewind = 0
                pressed = _enc.button(0)
                if pressed and not _btn_down:
                    _menu = (_menu + 1) % len(MENU_ITEMS)
                    _menu_flash = time.ticks_add(now, 2000)
                    _rewind = 0
                    _enc_accum = 0
                _btn_down = pressed
            except Exception:
                pass

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

        if _hit_flash:  # visual feedback for live-fired notes
            _d.fill_rect(0, 108, 128, 3, 15)
            _hit_flash -= 1

        # knob feedback: bar + weather icon, while the menu flash lives
        if time.ticks_diff(_menu_flash, now) > 0 and not _rec_until:
            _draw_knob()

        # status bar
        if _level < 0.06:
            weather = 'calm'
        elif _level < 0.25:
            weather = 'breeze'
        elif _level < 0.6:
            weather = 'rain'
        else:
            weather = 'STORM'
        if not _running:
            weather = 'PAUZE'
        if _rec_until:
            tag_txt = 'REC'
        elif _have_sample:
            tag_txt = '*-' if _density <= 0 else '*%d' % _density
        else:
            tag_txt = '--'
        if _ext_active:
            bpm_txt = 'CLK%3d' % int(_ext_bpm + 0.5)  # following Arturia
        else:
            bpm_txt = '%3d' % int(tulip.seq_bpm() + 0.5)
        if _rewind and time.ticks_diff(now, _rewind_t) > 1500:
            _rewind = 0  # gesture abandoned
        _d.fill_rect(0, 114, 128, 14, 0)
        if _rewind and not _rec_until:
            _d.text('REC? ' + '<' * min(6, _rewind), 4, 118, 15)
        elif time.ticks_diff(_menu_flash, now) > 0 and not _rec_until:
            if _menu == 0:
                val = '-' if _density <= 0 else str(_density)
            elif _menu == 1:
                val = str(_tone_lvl)
            elif _menu == 2:
                val = str(_echo_lvl)
            elif _menu == 3:
                val = str(_verb_lvl)
            else:
                val = str(_breath)
            _d.text('%s %s' % (MENU_ITEMS[_menu], val), 4, 118, 15)
        else:
            _d.text('%-6s %s %s' % (weather, bpm_txt, tag_txt), 4, 118, 15)

        amyboard.display_refresh()
    except Exception as e:
        _errors += 1
        if _errors <= 3:
            print('loop error:', e)


setup_weather_lfo()

try:
    midi.add_callback(_on_midi)
except Exception as e:
    print('midi callback failed:', e)

# ---- our own heartbeat: a background thread drives _service every 30 ms.
# NOT machine.Timer: hardware timer 3 collided with the firmware and took
# the whole USB stack down (learned 2026-07-28, the hard way).
_svc_pending = False


def _heartbeat():
    global _svc_pending
    while True:
        if not _svc_pending:
            _svc_pending = True
            try:
                micropython.schedule(_service, 0)
            except RuntimeError:
                _svc_pending = False  # scheduler queue full; try next tick
        time.sleep(0.03)


try:
    _thread.start_new_thread(_heartbeat, ())
    print('heartbeat thread running (30 ms)')
except Exception as e:
    print('heartbeat failed:', e)

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
