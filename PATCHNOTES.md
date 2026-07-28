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

## 2026-07-28 (middag) — v0.8 t/m v0.10: MIDI, de grote bevriezing, en speelbaarheid

- **Repo live**: github.com/sierkvdv/Amyboard_V1 (main); map opgeruimd (tests/, tools/, archive/), README met alle firmware-gotchas, patchkaart.html als Artifact gepubliceerd.
- **v0.8**: BeatStep via TRS MIDI in (met Sierks koptelefoonkabel!): FA/FC = start/stop (RESET_TIMEBASE op play = downbeat op de druk), noten vullen melodie-buffer → chops volgen Sierks toonhoogtes. Bewust GEEN external_midi_sync (bevriest de sketch, bewezen).
- **DE GROTE BEVRIEZING ONTLEED**: zodra MIDI-clock (F8) binnenstroomt, wordt de fabrieks-loop() nooit meer aangeroepen (ticks lopen — zelfs BSP-lock-step! — maar frames staan stil, MIDI-callbacks leven door). Fabrieks-loop = onbruikbaar bij externe clock.
- **v0.9 RAMP**: machine.Timer(3) als eigen hartslag → botst met firmware → USB compleet weg. Redding: RST kort, dan direct BOOT ~5s vasthouden (BOOT tijdens ínpluggen = ROM-bootloader, dat is de verkeerde noodstand!).
- **v0.9.1 DE FIX**: `_thread` achtergrond-draadje (30ms) + micropython.schedule drijft _service(); fabrieks-loop() = no-op. Kanarie-getest, overleeft volle MIDI-stroom. DE architectuur voortaan.
- **v0.10**: elke binnenkomende noot (alle kanalen: SEQ1/SEQ2/drums/pads) vuurt het sample direct af op die toonhoogte, velocity-gevoelig, óók tijdens PAUZE (solo-modus). Witte flits-streep onderin = visuele ontvangst-bevestiging.
- **Knop-update**: density 0-12; helemaal links (0, scherm `*-`) = machine-laag stil — Sierks verzoek toen zijn ene SEQ2-noot verzoop. "Begint ergens op te lijken."
- Volgende: mixer-test (RCA→minijack in line in; pas op rondzing-lus), stereo-kabel bestellen, effect-macro's/droog-stand, drone-laag, PCM_LEFT/preset-1024/loop-starvation bugs melden bij Shore Pine.

## 2026-07-28 (middag) — v0.11: karakter-knop + REVERSE-SPOKEN in de midden-zone ✅

- **Knop stuurt karakter, niet alleen aantal** (Sierk: "wordt wel gekker maar nog wel beetje zelfde"): interval-palet groeit mee met density (±5 → +kwinten → +7 → +tertsen), octaafsprong-kans stijgt, her-rol elke 4/2/1 maten (density ≤4/≤8/erboven), per-hit vlaag-noten (±5/±7, 1-op-8 bij density ≥5) en micro-drift ±15 cent zodat herhaalde slagen nooit identiek klinken.
- **REVERSE (Sierks wens: "in het midden reverse ofzo, daarbuiten niet")**: tijdens elke vangst draait een tweede vanger mee — 1 s lang `amy.get_input_buffer()` strak pollen (1024 B = 256 stereo-frames, ~172 blokken/s, dedup op inhoud), daarvan blok-voor-blok een omgekeerde mono-kopie op 22,05 kHz bouwen en uploaden via `amy.load_sample_bytes(..., preset=41, sr=22050)`.
- **Geheugen-les (2× MemoryError)**: één grote join van 347 KB kán niet op deze heap, en zelfs 87 KB naast de vastgehouden blokken niet → venster naar 1 s en de omkering blok-voor-blok rechtstreeks in een kleine buffer schrijven. `tests/bench_reverse.py` bewijst de timings op het board: capture 171/172 blokken, build 525 ms, upload 244 ms.
- **Gedrag**: alleen in de midden-zone van de knop (density 5-8) wordt ~35% van de hits omgekeerd afgespeeld (preset 41 i.p.v. 40); links en rechts daarvan blijft alles vooruit. Geen reverse-materiaal (oude vangst) = gewoon vooruit.
- Gedeployed en levend: "versie: v0.11 | leeft: True | errors: 0". Oor-test door Sierk staat nog open (knop naar `*5`-`*8`, verse vangst, luister naar achteruit-spoken tussen de beats).

## 2026-07-28 (middag) — v0.12: KNOP-MENU — effecten eindelijk speelbaar ✅

- Sierks verzoek: "handig als je met clicken door menutje kan om effecten te veranderen... en als je helemaal naar links draait paar seconden moet die opnieuw gaan opnemen."
- **Klik = menustap** door 4 items: `STORM` (density 0-12, incl. reverse-zone 5-8) → `ECHO` (0-10, 0 = droog) → `GALM` (reverb 0-10, 0 = droog) → `ADEM` (filter-ademdiepte 0-10, 0 = stil). **Draaien = waarde** van het actieve item. Statusbalk toont 2 s lang "ITEM waarde" na elke klik/draai.
- Dit lost de oude klacht op ("er speelt constant soort effect overheen waar we niks in kunnen wijzigen, erg saai"): echo en galm kunnen nu tot volledig droog.
- **Opnieuw opnemen = doordraai-gebaar**: als de waarde al op de bodem staat en je blijft naar links draaien (6 extra klikjes binnen ~1,5 s), start een verse vangst. Scherm toont `REC? <<<` als voortgang; loslaten = gebaar vervalt. Klik neemt dus níet meer op.
- Effect-calls zijn exact dezelfde als in setup_audio() (amy.echo/amy.reverb/filter_freq-mod), alleen het level verandert — geen nieuwe API's verzonnen.
- Board-verificatie: v0.12 boot schoon (errors 0, frames lopen), alle drie _apply_fx-calls draaien zonder fout terwijl de machine doorloopt. Oor-test Sierk: staat open (klik 1× → ECHO, draai naar 0, hoor 'm droog worden).

## 2026-07-28 (middag) — v0.13: knop-feedback op het scherm (het zonnetje) ✅

- Sierks verzoek: "als je aan het knopje draait moet dit ook visuele weergave... zonnetje die draait ofzo en minder fel wordt, verzin iets leuks."
- **Positiebalk** verschijnt 2 s bij elke draai: rail met cursor, spookzone (STORM 5-8) als grijs blok gemarkeerd, `<` links van de balk = doordraaien-is-opnemen-hint.
- **Weer-icoon per menu-item**: STORM = zonnetje met draaiende stralen dat dooft en stralen verliest naarmate je opendraait (15→3 helderheid, 8→2 stralen); in de spookzone draait het **achteruit** met `<<`-tekens ernaast; vanaf 9 draait het dubbel zo snel. ECHO = wegstervende blokjes (0 = "dry"). GALM = uitdijende ringen. ADEM = ademend vierkant (integer-driehoeksgolf, ademdiepte = knopwaarde).
- Implementatie zonder float-rekenwerk per frame: vaste 16-punts cirkeltabel (`_CIRC`), geen math-import nodig.
- Board-verificatie: alle vijf takken (STORM 6, STORM 12, ECHO 0, GALM 9, ADEM 7) live gerenderd op het scherm, errors bleef 0, defaults teruggezet.
- **Patchkaart volledig geherstyled** als boutique-merk (Error Instruments-energie): WM-1 wordmark met flikkerende bliksem, sticker-badges, faceplate met schroeven, knop-menu-diagram met zonebar, OLED-mock-schermregels, serienummer-strip met barcode. Zelfde Artifact-URL, print-stylesheet behouden. README + PATCHNOTES bij t/m v0.13.
- **v0.13.1**: knop op halve snelheid (Sierk: "gaat te snel, minimaal 2x zo langzaam") — 2 detents = 1 stap, rest wordt onthouden dus geen verloren klikjes; opname-gebaar daarop afgestemd (4 halve stappen ≈ 8 detents doordraaien); klik reset de rest-teller.

## 2026-07-28 (namiddag) — v0.14 + v0.15: tikjes, TONEN en een onmisbare menu-box ✅

- **v0.14 — hit-lengte volgt de STORM-knop** (Sierk: "wordt al erg druk als er pas 1 beat wordt aangetikt, hij speelt hele sample af... moet gewoon 1 tikkie doen die uitfadet"): machine-hits krijgen een getimede note-off — calm (1) ≈ 125 ms tikje, verder open = langere flarden (80 + density×45 ms), vanaf 9 klinkt het sample vol uit. De echo/galm verzorgen de uitfade van het tikje. Live pad-noten blijven wél vol klinken (pending cut op een hergebruikte osc wordt geschrapt). Implementatie: `_cuts`-lijst met (osc, deadline), elke service-pass afgehandeld met bewezen `vel=0`-sends — geen envelope-API-gok.
- **v0.15 — TONEN + grote menu-box** (Sierk: "merk niet super veel verschil... niet zo duidelijk als ik er doorheen klik... schuif toevoegen die wat cools kan, lekker die tonen beetje wisselen"):
  - Nieuw menu-item **TONEN** (0-10, start 3), tussen STORM en ECHO: elke maat verschuift het hele beat-patroon van toonhoogte — palet groeit met de knop van (0) via ±2/±5 naar ±12 (octaaf). 0 = blijft strak bij je melodie.
  - **Menu-box** midden op het scherm bij elke klik/draai: itemnaam + waarde + 5 positie-stipjes — je ziet nu onmiskenbaar wáár in het menu je zit. Icoontjes verhuisd naar onder de box; TONEN-icoon = drie huppelende nootjes (spronghoogte = knopwaarde).
  - **ADEM hoorbaar gemaakt**: ademt nu sneller én dieper naarmate je opendraait (LFO 0,05→0,35 Hz, diepte tot 1,25 octaaf) — voorheen alleen onhoorbaar-traag dieper.
- Board-verificatie: v0.15 boot schoon, alle 5 menu-widgets gerenderd, fx-calls foutloos, errors 0. Oor-test: STORM op 1-2 zetten (korte tikjes), dan TONEN opendraaien en de beats horen zwerven.
- **v0.16.1/2 — soepele knop + 5 stemmen**: encoder werd alleen in de trage teken-lus gepolst (~320 ms) → snelle draaien kwamen als bursts van 2-3 stappen binnen ("weer erg gevoelig"). Nu elke 30 ms-pass gepolst + burst-klem (max 2 stappen per keer, rest weggegooid — geen naijlen na de blokkende vangst-seconde). Chop-stemmen 3→5: stem-diefstal (herstart midden in golfvorm = tikje) veel zeldzamer. Kabel-episode: "kraakt heel erg + recordt niet" bleek géén code — input was volledig weg (level 0,01, piek ~60); na kabelherstel level 0,58-0,83. Resterende soms-klikjes: verdenk wash-oversturing bij harde passages (×6 gain); zo nodig gain omlaag.
- **v0.16 — pads klinken zolang je ze vasthoudt** (Sierk: "als je een kwart maat aantikt hoef ik 'm geen 3 seconden te horen, alleen als ik 3 seconden ingedrukt hou"): note-offs van de BeatStep worden nu verwerkt — loslaten = 150 ms fade. Kort tikken = kort geluidje, vasthouden = doorklinken (met het pitch-bewuste einde-venster als vangnet). `_live`-administratie koppelt gespeelde noten aan oscs; machine-hits en stilte() ruimen gestolen stemmen netjes op. Simulatie-bewezen op het board (press → live=[(60,112)], release → live=[], errors 0).
- **v0.15.5 — aanslag = lengte** (tussenstap, meteen vervangen door v0.16's vasthoud-gedrag als primaire lengteregelaar).
- **v0.15.4 — einde-klik weg**: losse tikjes bij het afspelen = het rauwe EINDE van de opname (stopt midden in een golf). Elke hit fadet nu pitch-bewust uit vlak vóór het sample-einde (hoge hit = korter venster: dur = base/2^((n-60)/12) − 200 ms; base 2000 vooruit / 1000 reverse); 9+ en pads klinken bijna vol uit en faden dan. Reverse-kopie krijgt ingebakken fade-randjes (256/512 samples) bij het bouwen. Kraak-episode verklaard: de "veel erger"-kraak was een vervuilde testvangst (kraak zat ín de sample); verse vangst loste het op.
- **v0.15.3 — vangst-kraak weg**: de reverse-vanger pollde non-stop en verhongerde de audio-taak precies tijdens REC (= als muziek binnenkomt na stilte, want dan vuurt de auto-vangst) → 2 ms slaapje per poll, vangst mist vrijwel niks.
- **v0.15.2 — restjes geklik + zeldzame "zap"**: (1) 8 ms attack-ramp in bp0 (`'8,1.0,150,0'`) — een 0 ms-start midden in een golfvorm klikte op de kóp van elke tik; (2) machine-hits geklemd op noot 36-84: melodienoot + octaafsprong + TONEN-shift + vlaag kon optellen tot ~20× afspeelsnelheid = raar chirp-zapje ("gek storinkje"). Live pads bewust niet geklemd. NB: valt een storinkje samen met `REC` op het scherm, dan is het de auto-vangst (bedoeld gedrag).
- **v0.15.1 — gekraak weg** (Sierk: "hoor nu beetje gekraak"): de harde vel=0-knip midden in de golfvorm kraakte. Fix: 150 ms release-envelope op de chop-oscs (`bp0='0,1.0,150,0'` + `amp={'const','vel','eg0'}`) — de getimede note-offs faden nu uit i.p.v. knippen. **Oor-bewezen via A/B-test op het board** (A hard / B fade): "klinkt weer goed, geen gekraak meer." Bonus: machine-hits zijn nu velocity-gevoelig; pauze-stop en stilte() faden ook zacht. Belangrijk AMY-feit: amp-coëfficiënten combineren multiplicatief — `amp={'const':3.5}` alléén = constante gain zonder envelope (daarom knipte het), const×vel×eg0 = wel envelope.
