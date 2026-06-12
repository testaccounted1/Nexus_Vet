# NEXUS v0.4 — Veteran Disability Claims Education Tool

Free, nonprofit, 100% local. No network access, no telemetry, no
monetization — ever.

> **⚠ Filing a false or exaggerated VA claim is a federal crime**
> (18 U.S.C. § 287; 38 U.S.C. § 6102). NEXUS supports legitimate,
> honest claims only. Educational tool — not a lawyer, doctor, or
> accredited representative. You own what you file.

## Build the desktop app + installer (Windows)

1. Install Python 3.10+ from python.org (check "Add to PATH").
2. Double-click **build_windows.bat**.
3. Results:
   - `dist\NEXUS\NEXUS.exe` — portable app, runs anywhere
   - `installer_out\NEXUS-Setup-0.4.0.exe` — full installer with
     desktop shortcut (requires free Inno Setup 6; the script tells
     you if it's missing)

The installer is **per-user** — no administrator rights needed.
Claim data is stored in `%APPDATA%\NEXUS` and survives uninstall
(it's the veteran's evidence record).

Run from source instead: `pip install PySide6` then `python qt_main.py`.

## Modules

- **Claim Roadmap** — the complete DIY filing path, $0 at every step
- **Evidence Vault** — per-condition checklists with gap flags
  ("tinnitus claimed, no audiogram on file"), claim summary export
- **Rating Calculator** — combined ratings (38 CFR 4.25) + bilateral
  factor (4.26), step-by-step, unit-tested against the official table
- **Benefits Explorer** — schedular, TDIU, SMC, CRDP/CRSC, Ch. 35,
  VR&E, funding-fee exemption, state benefits
- **C&P Exam Prep** — accurate, complete, honest
- **Glossary** — 20 terms in plain English

## Accessibility (designed for ages 18–95)

- **A− / A+** text scaling (85%–175%), persists between sessions
- **High-contrast mode** (black/white/gold)
- Large click targets, full keyboard navigation, visible focus rings
- Plain language throughout; one idea per screen

## Integrity design

1. Disclaimer gate on **every** launch; persistent fraud-warning bar.
2. Teaches evidence requirements — never symptoms to report.
3. C&P prep: "describe accurately, worst days included" — no scripts.
4. Gap flags name missing *documents*, never suggested *content*.
5. Everything stays local; data never touches a server.
6. The app educates and organizes but does not fill VA forms or draft
   statements — that line separates education from unaccredited
   claims assistance (38 U.S.C. § 5901). Have a VA-accredited
   attorney review content before public release.

## Tests

- `python test_va_math.py` — math engine vs. official table
- Headless UI smoke tests run via `QT_QPA_PLATFORM=offscreen`

`legacy_tkinter/` contains the v0.2 zero-dependency build.
