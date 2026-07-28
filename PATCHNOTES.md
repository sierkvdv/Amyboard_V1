# Patchnotes — Weermachine (working title)

## 2026-07-27 — Stap 0 + M0 voorbereid

- Docs geverifieerd (tulipcc/docs/amyboard, shorepine/amy, amyboard.com) via research-run; alle API-namen bevestigd, niets verzonnen.
- Board bereikbaar via `python -m mpremote resume connect COM4` (LET OP: altijd `resume`, zonder crasht de seriële verbinding op soft-reset).
- Firmware op board: 2026-06-04 build (MicroPython v1.24.0-preview, "AMYboard with ESP32S3").
  - Aanwezig en getest: `amyboard.cv_out/cv_in/set_cv_out`, `tulip.external_midi_sync` (enable+disable OK), `tulip.seq_add_callback/seq_ticks/seq_bpm/defer`, `midi.add_callback`, `amy.AUDIO_IN0`, `amy.send/reset/millis/send_raw`, `sequencer.tempo`, wire-keywords `tempo`/`sequence` (PPQ=48).
  - Ontbreekt (nieuwere firmware): `amyboard.set_midi_type`, `amyboard.report_version`, wire-keywords `sequencer_run`/`external_midi_sync` (wrapper in tulip werkt wél), `sequencer.start/stop`.
- M0-script klaar: `m0_hello_beep.py` (1 s sinus 440 Hz via gedocumenteerde time=-scheduling).

## 2026-07-27 — M0 GESLAAGD ✅

- Sierk hoort de beep-loop (sinus 440 Hz, 1/sec) via koptelefoon in line out (rij 2 rechts, USB-C-kolom).
- DIP-switches alle 4 OFF (line-level). Workflow definitief: mpremote via COM4, Sierk = oren/handen.
- Paneelindeling bevestigd (foto in docs): 5 rijen × 2 kolommen vanaf USB-C-kant: S/PDIF, LINE, MIDI, CV1, CV2; links=in, rechts=out.
- Volgende: M1 clock-lock (BeatStep Pro → MIDI in = rij 3, linkerkolom).

## 2026-07-27 — M1 mechanisme bewezen + firmware-drama + M2 desk-helft ✅

- **Firmware-upgrade** (web-editor, bootloader-ritueel RST/BOOT): 2026-06-04 → 2026-07-26 build. Board zit nu op **COM5** (was COM4). Nieuwe API's aanwezig: set_midi_type, report_version, wire sequencer_run/external_midi_sync.
- **M1 clock-lock BEWEZEN**: board volgde BeatStep Pro exact (100.0 bij display 100; 125.0 na live knopdraai naar 125) via USB-MIDI-brug (midi_bridge.py, desktop mido) + tulip.external_midi_sync(True).
- **MAAR: firmwarebug gevonden** — USB-MIDI-gadget-ontvangst van het board loopt na enkele minuten continu verkeer vast (ook met gefilterde brug zonder aftertouch; serial blijft werken; reboot herstelt). Vóór upgrade was USB-MIDI zelfs volledig dood. → Melden bij Shore Pine. **Oplossing: TRS-kabel (stereo minijack) → MIDI in**; staat op Sierks bestellijst. Bridge = alleen stopgap.
- BeatStep Pro speelt DRUM=ch10, SEQ1=ch1, SEQ2=ch2; pads sturen polytouch-stromen (bridge filtert die er nu uit).
- **M2 desk-helft klaar**: CV-loopback-kalibratie met mono-patchkabel. Alle 4 CV-jacks gezond, ruis ~8mV. Fits in calibration.json. ADC-ingangen satureren bit-identiek op +5,648V (meetlat-plafond, mogelijk USB-voeding-gerelateerd; DAC boven +5,6V onbewezen). Rack-voeding-test volgt bij verhuizing.
- **Sierks 2600 = Behringer clone**: gate-drempel +4V (QSG), envelope vuurt op gate alleen → spanningszorgen weg.
- Preview-demootje (drone+arp interne clock) draaide; Sierk vond het (terecht) te herhalend — generatief komt in M3. OLED-display-API gevonden (128×128, 16 grijs, amyboard.display.text/fill_rect/hline/vline + display_refresh + draw_waveform).

## 2026-07-27 (middag) — WASH live + weerscherm v0.3 gedeployed ✅

- **WASH-laag werkt**: pc line-out (groene jack achterop) → mono patchkabel → board line in. Debugsaga: Windows stuurde audio naar Jabra/BT-koptel (default device!); na omzetten naar "Speakers (Realtek)" vol signaal (~20k van 32k). Zenith DIY-synthje bleek zelf stil (nooit geflasht?) — terzijde gelegd.
- Wash-keten: AUDIO_IN0-osc (osc 100) gain ×6, ademend LPF24 (LFO osc 101, 0.05 Hz, ±0.35 oct — Sierk wilde 'm trager/subtieler), chorus 0.6, kwartnoot-echo 500ms fb 0.6, reverb 0.8/0.97. Suis = pc-ruisvloer + USB-aardlus ×gain (hardware-realiteit, geen bug; wordt beter met hetere bron).
- **sketch v0.3 = resident**: wash-audio + weerscherm — regen-dichtheid volgt loudness (EMA van input-peak, 8000≈luid), bliksem op transiënten (peak >2600 én >2.6×gemiddelde, cooldown), statusbalk calm/breeze/rain/STORM + BPM. Frame-limiter 70ms (~8-13 fps). Getest: stormtest max level 1.00, 29 drops, bliksem ✓, 0 errors.
- Reviewer (1, conform kostenregel) vond echte bug: bliksem-jog kon buiten scherm tekenen → gefixt met jog-clamp. Display-init + bootface nu ook try/except (faceless boot mag audio niet killen).
- **Debug-goudmijn ontdekt**: sketch draait als module `sketch` → `sys.modules['sketch']._frame/_level/_errors` live uitleesbaar via REPL. Loop-cadans gemeten: ~8 fps door runtime gedreven.
- Boot-marker: sketch schrijft /user/current/weermachine_boot.txt bij start.
- VOLGENDE: Sierk terug → visueel oordeel weerscherm; sample-catch (start_sample/SAMPLE_FROM_AUDIO_IN); TRS-kabel bestellen (M1-afronding); Juno-patch-tour voor drone-keuze; daarna M3 generatieve SEQ.

## 2026-07-27/28 (avond/nacht) — STORMVANGER WERKT ✅ (v0.5, na epische bugjacht)

- **EINDRESULTAAT**: v0.5 resident — auto-vangst bij binnenkomend geluid (REC op scherm), knop-klik = verse vangst, knop-draai = intensiteit (2-12), beats vuren op achtsten via de sequencer-tick-klok, patroon hussalt elke 4 maten, beats spelen door als muziek stopt. Sierk: "nice hij doet t !!"
- **HOOFDBUG van de avond**: `start_sample(preset=1024, ...)` — la 1024 (uit de docs!) is op firmware 2026-07-26 een ONGELDIGE opname-la: opname verdwijnt geluidloos. **Lage preset-nummers werken** (30/40 getest, ear-proven dubbele val: line-in-opname én output-opname beide afspeelbaar). Docs-firmware-mismatch → melden bij Shore Pine.
- **Tweede les**: afspelen van eigen opnames alleen bewezen met `wave=amy.PCM` (mix); PCM_LEFT op opgenomen presets nooit hoorbaar bevonden — vermijden tot upstream bevestigd.
- **Derde les**: sequence-geplande PCM-events bleven onbetrouwbaar (mede vervuild door de lege-la-bug; scheduled sine werkte na RESET_SEQUENCER+sequencer_run=1, "tabel-verstopping" door massa-deletes van niet-bestaande tags is óók reëel). v0.5 gebruikt de planner NIET meer voor chops: **beat-engine vuurt direct vanuit loop()** op achtste-grenzen uit tulip.seq_ticks() — alleen bewezen onderdelen.
- Fabrieks-PCM-presets (0/1/2 kick/snare) bevestigd hoorbaar → afspeel-engine altijd al OK geweest; alles wat stil bleef was lege la of verkeerde wave-stand.
- v0.4-tussenstappen: encoder werkt (klik+draai gedetecteerd, `amyboard.encoder()`), FRAME_MS 70→160 voor REPL-lucht (board wordt onder vollast stroperig traag met verbinden — bekende work-around: vers na reboot is het raam vlot; machine.reset() via exec werkt).
- A-tot-Z-demo-mysterie verklaard: vuurde 64 hits in de lege la 1024 met PCM_LEFT — dubbel dood spoor.
- OPEN: effecten-macro's (Sierk vindt vaste galm/echo "saai, niks te wijzigen" → knop/scenes + droog-stand), REC→*n indicator versimpelen, TRS-kabel voor BeatStep-clock (dan beats op zijn tempo i.p.v. vaste 120), Juno-drone-tour, bug reports upstream (preset-la + USB-MIDI-wedge).

## 2026-07-28 (nacht) — v0.6: ARTURIA-CLOCK-VOLGER via CV! ✅

- Sierks idee: BeatStep Pro **CLOCK OUT (analoge pulsen) → CV1 in** met mono-patchkabel — géén MIDI/TRS nodig! Pulsmeting: cv_in haalt ~10.000 samples/s in strakke lus; BSP stuurt 1 puls per 16e (~2,5V hoog, met na-trillingen/ringing tot -10V!).
- v0.6: `_clock_follow()` burst-sampelt CV1 12ms per loop-pass, edge-detect met **70ms debounce** (ringing gaf spook-intervallen van 54-60ms), tempo = 60000/(4×kleinste plausibele interval), EMA 0.15, apply 2×/s, terugval naar 120 BPM na 2,5s stilte. Statusbalk toont `CLK <bpm>` bij extern volgen.
- Getest: BSP display 200 → CLK ~203 gevolgd; draaien volgt binnen seconden. "Muzikaal strak" (meedeinend), niet sample-strak — dat wordt de TRS-MIDI-kabel (M1-afronding).
- Sessie-einde: volledig instrument op bureau — wash + weerscherm + auto-vangst + knop (vang/intensiteit) + Arturia-tempo-volger. Werktitel Weermachine houdt stand.
