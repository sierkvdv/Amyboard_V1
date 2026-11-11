# weermachine — AMYboard soundscape-brein (werktitel; paneelkaart heet WM-1)

Tempo-locked instrument in MicroPython op de AMYboard (ESP32-S3, AMY-engine), gelockt op BeatStep Pro MIDI-clock: SEQ (CV/gate naar de ARP 2600), DRONE (AMY-drones), WASH (line-in door AMY-effecten). Repo `sierkvdv/Amyboard_V1`. Bouwlog `PATCHNOTES.md`, firmware-gotcha's `README.md`, paneelkaart `patchkaart.html` (live op https://synthesizer.sierk.dev, bijwerken = `python tools/build_web.py` + scp + chown; VPS `/srv/apps/synthesizer/public/index.html`). Vaste regels: `~/.claude/CLAUDE.md`.

## Werkwijze
- Sierk is oren en handen (patcht, plakt code, zegt wat hij hoort); ik schrijf code en zeg exact wat te patchen en te verwachten. Nederlands praten, code en comments Engels. Milestones M0–M7; elke stap eindigt met een test die Sierk doet.
- Spanningsveiligheid eerst (DIP-switches, bereiken checken vóór patchen). Docs winnen van het plan; nooit API-namen verzinnen (github.com/shorepine/tulipcc/docs/amyboard, github.com/shorepine/amy, amyboard.com). Push na elke werkende milestone. Max 1 reviewer.

## Hardware
AMYboard (2× CV in ADS1015 12-bit ±10V, 2× CV uit GP8413 ±10V, TRS MIDI, line/S-PDIF I/O, DIP line 1Vpp vs 10Vpp = alleen audio, microSD, 4-bit OLED). BeatStep **Pro** (MIDI naar AMYboard = gewone stereo-minijack). 2600 = **Behringer** (gate-drempel +4V; origineel wil ~10V). Board op COM5 (eerder COM4; checken), draait standalone op elke USB-lader.

## Workflow op de pc
- `python -m mpremote resume connect COM5 exec/run/fs cp` — altijd `resume` (zonder: soft-reset → SerialException). Web-editor (amyboard.com/editor, Chrome, "Control your AMYboard") niet tegelijk gebruiken (poortconflict).
- Persistent = `/user/current/sketch.py` (auto-run bij boot); fabrieksbackup `factory_sketch_backup.py`. Recovery: BOOT ingedrukt bij opstarten = sketch overslaan + selftest. RST kort → BOOT ~5 s = redding na USB-dood; BOOT tijdens inpluggen = ROM-bootloader.
- Boot-sketch draait als module `sketch`: `sys.modules['sketch'].<global>` vanaf de REPL. Onder vollast wordt de REPL stroperig; `machine.reset()` via exec is een prima herstart.

## Kernarchitectuur (v0.15)
`_thread`-heartbeat (30 ms) + `micropython.schedule` drijft alles; fabrieks-`loop()` = no-op (verhongert zodra MIDI-clock binnenkomt). `machine.Timer(3)` = USB-dood, niet gebruiken. Beats plannen NIET via sequence-events voor PCM; beat-engine checkt `tulip.seq_ticks()//24 % 8` en vuurt direct. Knop-UX: klik = menu STORM/TONEN/ECHO/GALM/ADEM, draai = waarde (2 detents = 1 stap), doordraaien voorbij 0 = `REC?`.

## Geverifieerde API-feiten en gotcha's (niet opnieuw uitzoeken)
- **0xF8 MIDI-clock bereikt Python nooit** (C consumeert 'm). Clock-lock = `tulip.external_midi_sync(True)` (48 PPQ lock-step). 0xFA/FB/FC komen wél via `midi.add_callback`; transport zelf afvangen en `amy.send_raw('zY1Z'/'zY0Z')`.
- In follow-mode zonder clock staan seq-callbacks én `tulip.defer` stil → free-run-fallback vereist stall-detectie buitenom + `external_midi_sync(False)`.
- 1V/oct zonder polling: `amy.send(freq={'ext1':1})`; `amyboard.set_cv_out(channel, synth)` = synth-audio → CV-out (tempo-synced LFO als AMY-osc); `cv_trigger` wire-param.
- MIDI-in accepteert TRS A én B; software-A/B is alleen MIDI-uit.
- Audio-in als osc: `wave=amy.AUDIO_IN0/1`; capture staat standaard aan; `amy.get_input_buffer()` = 1024 bytes, 256 stereo-frames 16-bit LE. Echo in ms (default max_delay ~743 ms, verhogen). 4 FX-bussen (bus 0..3).
- Patches: 0-127 Juno, 128-255 DX7, 256 piano, 384-390 drums; `amy.send(synth=N, num_voices=M, patch=P)`, vel=0 = note-off.
- OLED: kleuren **0-15** (niet 0-255). Full refresh ≈ 70-90 ms. MicroPython: geen tuple-slicing met step.
- **Samplen**: `amy.start_sample(preset=N, source=amy.SAMPLE_FROM_AUDIO_IN, max_frames=F, midinote=60)`; preset MOET laag zijn (30/40 bewezen; 1024 uit de docs = opname verdwijnt geluidloos). Afspelen alleen `wave=amy.PCM` bewezen. Fabriekspresets 0-18 = 808 = smoke-test.
- **Headroom**: pc-line-in piekt ~20k/32k; elke gain-constante × piek < 32767, anders digitaal gekraak (wash 1,5 / hits 1,4 nu). Luidheid op de mixer regelen. I2C-encoder pollen op ~300 ms (30-60 ms = kraak); max 3 gelijktijdige PCM-stemmen bewezen.
- amp-coëfficiënten combineren multiplicatief: `amp={'const': X, 'vel': 1, 'eg0': 1}` met per osc éénmalig `bp0='0,1.0,150,0'`; `const` alleen + latere vel=0 = harde knip = kraak.
- Massa-deletes van niet-bestaande sequence-tags verstoppen de event-tabel; herstel = RESET_SEQUENCER + sequencer_run=1 + herplannen.
- Firmware 2026-06-04 heeft `amyboard.cv_out/cv_in/set_cv_out`, `tulip.external_midi_sync`, `tulip.seq_add_callback/seq_ticks/seq_bpm/defer`, `midi.add_callback`; ontbreekt: `set_midi_type`, `report_version`, `sequencer.start/stop`. Upgrade via editor of `amyboard.upgrade()` (WiFi).
- Bekende firmware-bugs om te melden bij Shore Pine: preset-1024, PCM_LEFT, loop-starvation, Timer-conflict, USB-MIDI-gadget wedged na minuten verkeer (daarom TRS).

## Open
Stereo-kabel voor sample-strakke opname, effect-macro's/droog-stand, drone-laag, bugs melden.

## Stand
- Stand: onbekend per 11-11-2026, laatste commit 24-09-2026. Open punten: zie "Open" hierboven.
