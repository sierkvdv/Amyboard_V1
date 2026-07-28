# STORMVANGER — live sample-catcher for the Weermachine.
# Catches a chunk of line-in audio into sample RAM, then forges new beats
# out of it: stutters, pitch ladders, half-speed drags, random chaos — all
# locked to the sequencer grid, all derived from the original material.
# IMPORTANT: never calls amy.reset() — the resident WASH keeps running.

import random
import time

import amy

CATCH_PRESET = 40  # low slot — 1024 per docs is invalid on this firmware
CHOP_OSCS = (110, 111, 112)  # rotated so hits can overlap without cutting
TAG_BASE = 300               # sequencer tags 300..339 belong to the catcher
PPQ = 48
BAR = PPQ * 4                # 192 ticks per 4/4 bar

_bpm = 120.0
_used_tags = set()  # only delete tags we actually scheduled — mass-deleting
                    # nonexistent tags clogs the sequencer event table!


def catch(beats=4, bpm=None, preset=CATCH_PRESET):
    """Record `beats` beats of line-in audio into `preset`.
    Blocks while recording (start_sample + wait + stop_sample)."""
    global _bpm
    if bpm:
        _bpm = float(bpm)
    seconds = beats * 60.0 / _bpm
    frames = int(44100 * seconds)
    amy.start_sample(preset=preset, source=amy.SAMPLE_FROM_AUDIO_IN,
                     max_frames=frames)
    time.sleep(seconds + 0.1)
    try:
        amy.stop_sample()
    except Exception:
        pass  # may have auto-stopped at max_frames
    amy.send(sequencer_run=1)  # sampling pauses the transport — restart it!
    print('gevangen: %.1f s (%d beats @ %.0f BPM) -> preset %d'
          % (seconds, beats, _bpm, preset))


def _clear_tags():
    for t in list(_used_tags):
        amy.send(sequence=',,%d' % t)
    _used_tags.clear()


def _hit(osc, note, vel, tick, period, tag):
    # amp boost so chops cut through the x6-boosted wash instead of drowning
    amy.send(osc=osc, wave=amy.PCM_LEFT, preset=CATCH_PRESET,
             note=note, vel=vel, amp={'const': 3.5},
             sequence='%d,%d,%d' % (tick, period, tag))
    _used_tags.add(tag)


def stutter(base=60):
    """Hard 16th-note retrigger of the catch — classic stutter."""
    _clear_tags()
    tag = TAG_BASE
    for i in range(8):  # 8 sixteenths = half a bar of machine-gun
        _hit(CHOP_OSCS[0], base, 0.9, i * 12, BAR, tag)
        tag += 1
    print('patroon: stutter')


def ladder(base=60):
    """Rising pitch ladder over one bar: origineel -> +5 -> +10 -> +15."""
    _clear_tags()
    tag = TAG_BASE
    for i in range(4):
        _hit(CHOP_OSCS[i % 3], base + 5 * i, 0.9, i * PPQ, BAR, tag)
        tag += 1
    print('patroon: ladder')


def drag(base=48):
    """Half-speed monster: octave down = half tempo, once per bar."""
    _clear_tags()
    _hit(CHOP_OSCS[0], base, 1.0, 0, BAR, TAG_BASE)
    print('patroon: drag (halve snelheid)')


def chaos(density=6, spread=12):
    """Random pattern, re-rolled every call: `density` hits per bar on
    random 16th slots, random pitch within +/- `spread` semitones."""
    _clear_tags()
    tag = TAG_BASE
    used = []
    for i in range(density):
        slot = random.randrange(0, 16)
        while slot in used:
            slot = random.randrange(0, 16)
        used.append(slot)
        note = 60 + random.randrange(0, 2 * spread + 1) - spread
        vel = 0.5 + random.randrange(0, 5) / 10.0
        _hit(CHOP_OSCS[i % 3], note, vel, slot * 12, BAR, tag)
        tag += 1
    print('patroon: chaos -', density, 'hits')


def stilte():
    """Stop all catcher patterns (the wash keeps running)."""
    _clear_tags()
    for osc in CHOP_OSCS:
        amy.send(osc=osc, vel=0)
    print('stormvanger stil')


print('STORMVANGER geladen: catch(beats), stutter(), ladder(), drag(), chaos(), stilte()')
