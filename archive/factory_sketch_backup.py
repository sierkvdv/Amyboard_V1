# AMYboard Eurorack Menu V20 DX7 MORPH
# Based on V19f Sweet Filter
#
# JUNO:
# - Original patch preview
# - Cutoff 0-500 step 5
# - Resonance 0-250
#
# DX7:
# - Original patch preview
# - Morph menu
# - Algorithm: 0 = ORIG, 1-32 = override
# - Feedback:  0 = ORIG, 1-100 = override
#
# Long press = back

import amy, amyboard
from patches import patches as PRESETS

SEESAW = 0x36
BTN_PIN = 24
SYNTH = 1
LONG_PRESS_TICKS = 10

amyboard.init_display()
amyboard.init_buttons(pins=(BTN_PIN,), seesaw_dev=SEESAW)

menus = {
    "MAIN": ["JUNO", "DX7", "WEAVER"],

    "JUNO": ["Patch", "Level", "Boost", "Envelope", "Filter", "FX"],
    "JUNO Envelope": ["Attack", "Decay", "Sustain", "Release"],
    "JUNO Filter": ["Cutoff", "Resonance"],
    "JUNO FX": ["Reverb", "Echo"],

    "DX7": ["Patch", "Level", "Boost", "Morph", "FX"],
    "DX7 Morph": ["Algorithm", "Feedback"],
    "DX7 FX": ["Reverb", "Echo"],

    "WEAVER": ["Record", "Chaos", "Grain", "Density", "Pitch", "Freeze"]
}

values = {
    "JUNO Patch": 0,
    "JUNO Level": 80,
    "JUNO Boost": 100,

    "JUNO Envelope Attack": 100,
    "JUNO Envelope Decay": 300,
    "JUNO Envelope Sustain": 70,
    "JUNO Envelope Release": 500,

    "JUNO Filter Cutoff": 200,
    "JUNO Filter Resonance": 80,

    "JUNO FX Reverb": 0,
    "JUNO FX Echo": 0,

    "DX7 Patch": 0,
    "DX7 Level": 80,
    "DX7 Boost": 100,

    # 0 = ORIG, 1-32 = override
    "DX7 Morph Algorithm": 0,

    # 0 = ORIG, 1-100 = override
    "DX7 Morph Feedback": 0,

    "DX7 FX Reverb": 0,
    "DX7 FX Echo": 0,

    "WEAVER Record": 0,
    "WEAVER Chaos": 50,
    "WEAVER Grain": 120,
    "WEAVER Density": 50,
    "WEAVER Pitch": 0,
    "WEAVER Freeze": 0
}

ranges = {
    "Patch": (0, 127, 1),
    "Level": (0, 100, 1),
    "Boost": (50, 200, 5),

    "Attack": (0, 5000, 100),
    "Decay": (0, 5000, 100),
    "Sustain": (0, 100, 1),
    "Release": (0, 5000, 100),

    "Cutoff": (0, 500, 5),
    "Resonance": (0, 250, 1),

    "Algorithm": (0, 32, 1),
    "Feedback": (0, 100, 1),

    "Reverb": (0, 100, 1),
    "Echo": (0, 100, 1),

    "Record": (0, 1, 1),
    "Chaos": (0, 100, 1),
    "Grain": (10, 1000, 10),
    "Density": (0, 100, 1),
    "Pitch": (-24, 24, 1),
    "Freeze": (0, 1, 1)
}

boosts = {}

current_menu = "MAIN"
menu_stack = []
cursor_stack = []
cursor = 0
edit_mode = False
active_engine = "JUNO"

last_enc = amyboard.read_encoder(seesaw_dev=SEESAW)
last_btn = False
press_time = 0
tick = 0
back_armed = False


def key_for(menu, item):
    return menu + " " + item


def root_engine(menu):
    if menu.startswith("JUNO"):
        return "JUNO"
    if menu.startswith("DX7"):
        return "DX7"
    return active_engine


def absolute_patch(engine):
    if engine == "JUNO":
        return values["JUNO Patch"]

    if engine == "DX7":
        return 128 + values["DX7 Patch"]

    return 0


def patch_name(engine):
    idx = absolute_patch(engine)

    if 0 <= idx < len(PRESETS):
        return PRESETS[idx].strip()

    return "???"


def restore_boost(engine):
    p = absolute_patch(engine)

    if p in boosts:
        values[engine + " Boost"] = boosts[p]
    else:
        values[engine + " Boost"] = 100


def remember_boost(engine):
    boosts[absolute_patch(engine)] = values[engine + " Boost"]


def apply_level(engine):
    level = values[engine + " Level"] / 100.0
    boost = values[engine + " Boost"] / 100.0

    amy.send(
        synth=SYNTH,
        volume=level * boost
    )


def reset_dx7_morph_values():
    values["DX7 Morph Algorithm"] = 0
    values["DX7 Morph Feedback"] = 0


def load_original_patch(engine):
    global active_engine

    active_engine = engine
    restore_boost(engine)

    amy.send(
        synth=SYNTH,
        patch=absolute_patch(engine),
        num_voices=6
    )

    apply_level(engine)


def load_dx7_original_and_reset_morph():
    reset_dx7_morph_values()
    load_original_patch("DX7")


def apply_dx7_morph_stack():
    # Safe morph method:
    # reload original DX7 patch first,
    # then apply active morph overrides.
    load_original_patch("DX7")

    alg = values["DX7 Morph Algorithm"]
    fb = values["DX7 Morph Feedback"]

    if alg > 0:
        amy.send(
            synth=SYNTH,
            algorithm=alg
        )

    if fb > 0:
        amy.send(
            synth=SYNTH,
            feedback=fb / 100.0
        )


def apply_juno_env():
    a = values["JUNO Envelope Attack"]
    d = values["JUNO Envelope Decay"]
    s = values["JUNO Envelope Sustain"] / 100.0
    r = values["JUNO Envelope Release"]

    bp = "0,0,%d,1,%d,%.2f,%d,0" % (a, d, s, r)

    amy.send(
        synth=SYNTH,
        bp0=bp
    )


def apply_juno_filter():
    cutoff = values["JUNO Filter Cutoff"]
    resonance = values["JUNO Filter Resonance"] / 100.0

    amy.send(
        synth=SYNTH,
        filter_freq=cutoff
    )

    amy.send(
        synth=SYNTH,
        resonance=resonance
    )


def apply_fx(engine):
    rev = values[engine + " FX Reverb"] / 100.0
    ech = values[engine + " FX Echo"] / 100.0

    amy.send(
        bus=0,
        reverb="%.2f,0.95,0.20,8000" % rev
    )

    amy.send(
        bus=0,
        echo="%.2f,500,500,0.50,0" % ech
    )


def value_unit(item):
    if item in ("Level", "Boost", "Sustain", "Resonance", "Reverb", "Echo", "Chaos", "Density"):
        return "%"

    if item in ("Attack", "Decay", "Release"):
        return "ms"

    if item == "Pitch":
        return "st"

    if item == "Grain":
        return "ms"

    return ""


def value_text(menu, item):
    k = key_for(menu, item)

    if menu == "DX7 Morph" and item == "Algorithm":
        v = values[k]
        if v == 0:
            return "ORIG"
        return str(v)

    if menu == "DX7 Morph" and item == "Feedback":
        v = values[k]
        if v == 0:
            return "ORIG"
        return str(v)

    if k in values:
        txt = str(values[k])
        unit = value_unit(item)

        if unit != "":
            txt += " " + unit

        return txt

    return ""


def draw_bar(value, item, y):
    mn, mx, step = ranges[item]
    width = 10

    if mx == mn:
        filled = 0
    else:
        filled = int(((value - mn) * width) / (mx - mn))

    if filled < 0:
        filled = 0

    if filled > width:
        filled = width

    bar = ""

    for i in range(width):
        if i < filled:
            bar += "#"
        else:
            bar += "-"

    amyboard.display.text(bar, 0, y, 255)


def draw_patch_screen():
    engine = root_engine(current_menu)
    local = values[engine + " Patch"]
    name = patch_name(engine)

    amyboard.display.fill(0)

    amyboard.display.text(engine[:16], 0, 0, 255)
    amyboard.display.text(str(local), 0, 18, 255)

    if len(name) <= 16:
        amyboard.display.text(name, 0, 38, 255)
    else:
        amyboard.display.text(name[:16], 0, 34, 255)
        amyboard.display.text(name[16:32], 0, 48, 255)

    amyboard.display_refresh()


def draw_edit_screen():
    item = menus[current_menu][cursor]

    if item == "Patch":
        draw_patch_screen()
        return

    k = key_for(current_menu, item)

    amyboard.display.fill(0)
    amyboard.display.text(item.upper()[:16], 0, 0, 255)

    if k in values:
        txt = value_text(current_menu, item)

        amyboard.display.text(txt[:16], 0, 24, 255)

        if item in ranges:
            draw_bar(values[k], item, 48)

    amyboard.display_refresh()


def show_back_screen():
    amyboard.display.fill(0)
    amyboard.display.text("BACK", 0, 18, 255)
    amyboard.display.text("release", 0, 42, 180)
    amyboard.display_refresh()


def draw():
    if edit_mode:
        draw_edit_screen()
        return

    amyboard.display.fill(0)
    amyboard.display.text(current_menu[:16], 0, 0, 255)

    items = menus[current_menu]
    start = cursor - 1

    if start < 0:
        start = 0

    if start > len(items) - 3:
        start = len(items) - 3

    if start < 0:
        start = 0

    y = 18

    for i in range(start, min(start + 3, len(items))):
        item = items[i]
        prefix = ">" if i == cursor else " "
        engine = root_engine(current_menu)

        if item == "Patch" and current_menu in ("JUNO", "DX7"):
            line = prefix + str(values[engine + " Patch"]) + " " + patch_name(engine)

        else:
            line = prefix + item
            k = key_for(current_menu, item)

            if k in values:
                line += ": " + value_text(current_menu, item)

        amyboard.display.text(
            line[:16],
            0,
            y,
            255 if i == cursor else 120
        )

        y += 16

    amyboard.display_refresh()


def apply_value(menu, item):
    engine = root_engine(menu)

    if item == "Patch" and engine == "JUNO":
        load_original_patch("JUNO")

    elif item == "Patch" and engine == "DX7":
        load_dx7_original_and_reset_morph()

    elif item == "Level" and engine in ("JUNO", "DX7"):
        apply_level(engine)

    elif item == "Boost" and engine in ("JUNO", "DX7"):
        remember_boost(engine)
        apply_level(engine)

    elif menu == "JUNO Envelope":
        apply_juno_env()

    elif menu == "JUNO Filter":
        apply_juno_filter()

    elif menu == "DX7 Morph":
        apply_dx7_morph_stack()

    elif menu == engine + " FX":
        apply_fx(engine)


def change_value(delta):
    item = menus[current_menu][cursor]
    k = key_for(current_menu, item)

    if k not in values:
        return

    mn, mx, step = ranges[item]

    values[k] += delta * step

    if values[k] < mn:
        values[k] = mn

    if values[k] > mx:
        values[k] = mx

    apply_value(current_menu, item)
    draw()


def preview_patch(delta):
    engine = root_engine(current_menu)
    k = engine + " Patch"

    values[k] += delta

    if values[k] < 0:
        values[k] = 0

    if values[k] > 127:
        values[k] = 127

    if engine == "DX7":
        load_dx7_original_and_reset_morph()
    else:
        load_original_patch(engine)

    draw_patch_screen()


def enter_item():
    global current_menu, cursor, edit_mode

    item = menus[current_menu][cursor]

    if current_menu == "MAIN":
        menu_stack.append(current_menu)
        cursor_stack.append(cursor)

        current_menu = item
        cursor = 0
        edit_mode = False

        if current_menu == "JUNO":
            load_original_patch("JUNO")

        if current_menu == "DX7":
            load_dx7_original_and_reset_morph()

        draw()
        return

    # Patch is direct preview.
    # Short press on Patch jumps to Level.
    if current_menu in ("JUNO", "DX7") and item == "Patch":
        cursor = 1
        edit_mode = False
        draw()
        return

    submenu = current_menu + " " + item

    if submenu in menus:
        menu_stack.append(current_menu)
        cursor_stack.append(cursor)

        current_menu = submenu
        cursor = 0
        edit_mode = False

        draw()
        return

    k = key_for(current_menu, item)

    if k in values:
        edit_mode = not edit_mode
        draw()


def go_back():
    global current_menu, cursor, edit_mode

    if edit_mode:
        edit_mode = False
        draw()
        return

    if len(menu_stack) > 0:
        current_menu = menu_stack.pop()
        cursor = cursor_stack.pop()
    else:
        current_menu = "MAIN"
        cursor = 0

    draw()


load_original_patch("JUNO")
draw()


def loop():
    global cursor
    global last_enc
    global last_btn
    global press_time
    global tick
    global back_armed

    enc = amyboard.read_encoder(seesaw_dev=SEESAW)
    delta = enc - last_enc

    if delta != 0 and not back_armed:
        last_enc = enc

        if not edit_mode and current_menu in ("JUNO", "DX7") and cursor == 0:
            preview_patch(delta)

        elif edit_mode:
            change_value(delta)

        else:
            cursor = (cursor + delta) % len(menus[current_menu])
            draw()

    btn = amyboard.read_buttons(
        pins=(BTN_PIN,),
        seesaw_dev=SEESAW
    )[0]

    if btn and not last_btn:
        press_time = tick
        back_armed = False

    if btn and not back_armed:
        if tick - press_time > LONG_PRESS_TICKS:
            back_armed = True
            show_back_screen()

    if last_btn and not btn:
        if back_armed:
            back_armed = False
            go_back()
        else:
            enter_item()

    last_btn = btn
    tick += 1

# Do not edit. Set automatically by the knobs on AMYboard Online.
_auto_generated_knobs = """
i1ic255Z
i1iv6in8Z
i1v0w8a,,,0.000f,,,1.000,,0.007b0.160L1o22O2,3,4,5,6,7A,,,1.000,0,1.000,0,1.000,731,1.000T2X3Z
i1v1a,,0.000f6.167P0.250Z
i1v2a0.459,,0.000P0.250I1.000L1A,0.000,97,0.917,0,0.917,530,0.500,70,0.000T2Z
i1v3a1.834,,0.000P0.250I1.001L1A,0.000,4,1.000,30,0.917,0,0.917,53,0.000T2Z
i1v4a2.000,,0.000P0.250I1.000L1A,0.000,4,1.000,30,0.917,0,0.917,53,0.000T2Z
i1v5a2.000,,0.000P0.250I0.998L1A,0.000,4,1.000,0,0.917,0,0.917,53,0.000T2Z
i1v6a0.648,,0.000P0.250I0.504L1A,0.000,11,0.229,26,0.707,37,0.771,52,0.000T2Z
i1v7a1.834,,0.000P0.250I0.504L1A,0.000,7,1.000,3,0.386,0,0.771,52,0.000T2Z
i1V0.800x0.000,0.000,0.000M0.000,500.000,,0.500,0.000k1.000,320.000,0.500,0.500h0.600,0.950,0.200,8000.000Z
"""
