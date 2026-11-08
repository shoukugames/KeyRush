# Key Rush

**Watch. Remember. Type it back!**

Key Rush is a memory and touch-typing game for the keyboard's home row, for ages **8+**.
The home-row keys light up one by one to an ambient beat. Repeat them in the same order,
like the classic Simon game. The rounds never end, and each one gets a little longer and faster.

Version **0.1.1**, released 2026-11-08. Plays in **English** and **Japanese (日本語)**. Created by **Shawn Rapaz** and made with **Claude Code**.
Website: <https://shoukugames.org/>. Email: <info@shoukugames.org>

## How to play

1. Rest your fingers on the home row: **A S D F** for the left hand, **J K L ;** for the right.
   The bumps on F and J help you find them without looking.
2. **WATCH:** keys light up and chime, one per beat.
3. **YOUR TURN:** type the same keys in the same order before the time bar runs out.
4. Get the sequence right and it comes back one key longer, just like Simon.

| Rule | |
|---|---|
| Sequence repeated correctly | **+100** points |
| Wrong key, or too slow | **-10** points and one heart lost. You then watch the same sequence again. |
| Hearts | 3. Lose them all and the game is over. |
| Rounds | Every 4 completed sequences moves you up a round (round 1, round 2...). The rounds never end. |
| Each new round | Faster tempo, less time per key, and every second round the sequences start one key longer |

Keys that aren't on the home row are ignored, and the game reminds you to keep your fingers in place.
Pressing keys while you're still watching doesn't count against you.

### Difficulty

| | Keys | Starting tempo | Time per key |
|---|---|---|---|
| **Easy** | D F J K | 72 BPM | 4.5 s, down to 1.6 s |
| **Medium** | A S D F J K L ; | 84 BPM | 3.5 s, down to 1.2 s |
| **Hard** | the whole row, G and H too | 96 BPM | 3.0 s, down to 0.9 s |

### Controls

| Key | Action |
|---|---|
| Arrows + Enter, or the mouse | Menus. Left and Right change the difficulty. |
| Home-row keys | Play |
| Esc | Pause (Q from the pause screen quits to the title) |
| M | Music on or off |
| L | Switch between English and 日本語 (title screen) |
| F11 | Full screen |

## Languages / 言語

Everything in the game is in both English and Japanese: menus, play messages, finger names,
the For Parents pages and the credits. Choose **LANGUAGE / 言語** on the title screen
(or press **L**). The first time it starts, the game picks Japanese on a Japanese system,
otherwise English. The choice is saved. The keys stay as the letters printed on the keyboard.

ゲームは英語と日本語に対応しています。タイトル画面の「言語」（または L キー）で切り替えられます。

## Title screen

- **Language**: English or 日本語.
- **Play**, and a **difficulty select** (Easy, Medium, Hard). Score and high score show at the top while you play.
- **Top 10**: a table for each difficulty. A Top 10 score asks for the player's name.
- **For Parents** has two pages:
  - *Progress*: total time played, time today, games played, key accuracy, best round,
    typing errors, time-outs, sequence failures, completed sequences, game overs, minutes
    played per day for the last week, scores of the last 15 games, and the best score for each difficulty.
  - *What went wrong*: a home-row heat map of missed keys, the most common mix-ups (for example
    "wanted F, pressed D"), the recent games with their errors, and a practice tip.
  - Press **Del** to reset the statistics. The Top 10 tables are kept.
- **Credits**: version, release date, creator, website, email and the license.

## Music and sound

All music and sound is made in code when the game starts. There are no audio files.
The music is a calm ambient pad on a slow chord loop, with a soft bass and gentle sparkles.
Each key plays its own bell note from a pentatonic scale, so every sequence sounds musical.
The game shows one key per beat and changes tempo on the beat, so the keys always land on
the music. Soft percussion is added layer by layer as the rounds go up.

## Install

| System | File | How |
|---|---|---|
| Debian / Ubuntu (64-bit) | `keyrush_v0.1.1_amd64.deb` | `sudo apt install ./keyrush_v0.1.1_amd64.deb`, then find **Key Rush** in your games menu or run `keyrush` |
| Windows 10/11 (64-bit) | `KeyRush-v0.1.1.exe` | Double-click it. Nothing needs to be installed. |

Saved data (scores, statistics, settings) is kept in `~/.local/share/keyrush/` on Linux
and in `%APPDATA%\KeyRush\` on Windows.

## Run from source

```bash
python3 -m pip install -r requirements.txt
python3 run_game.py
```

Needs Python 3.10 or newer.

## Build

```bash
./build.sh                     # both installers into dist/
packaging/build_linux.sh       # dist/keyrush_v<version>_<arch>.deb
packaging/build_windows.sh     # dist/KeyRush-v<version>.exe (built under Wine)
```

The Linux build needs `python3-venv` and `dpkg-deb`. The Windows build needs `wine`, `xvfb-run` and `curl`.
On its first run it installs Windows Python into a private Wine prefix in `build/`.
Each build script unpacks the result and plays a full automatic game with it (`--smoke-test`)
before it reports success.

For development:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest                       # rules, saved data and sound tests
python3 tools/screenshots.py [dir] [en|ja]   # a PNG of every screen (default build/screenshots)
python3 tools/make_icon.py              # redraw assets/icon.png and icon.ico
```

## Project layout

```
keyrush/
  logic.py     the rules: sequences, scoring, hearts, rounds, beat clock (no drawing, fully tested)
  audio.py     synthesised instruments, effects and the ambient music
  scenes.py    title, play, game over, Top 10, For Parents and credits
  keyboard.py  the on-screen home row
  ui.py        fonts, glows, panels, background and particles
  storage.py   Top 10, statistics and settings (JSON)
  i18n.py      English and Japanese text
  config.py    difficulty curves, rules and colours
packaging/     PyInstaller spec, .desktop file and build scripts
tests/         pytest suite
tools/         screenshots and icon generator
```

## Found a bug?

See [BUGREPORT.md](BUGREPORT.md).

## License

Copyright (C) 2026 Shawn Rapaz.

Key Rush is free software: you can redistribute it and/or modify it under the terms of the
**GNU General Public License v3.0** as published by the Free Software Foundation, either
version 3 of the License or (at your option) any later version. It is distributed WITHOUT
ANY WARRANTY. See [LICENSE](LICENSE).

The font M PLUS 1p is under the SIL Open Font License, which is included at
[assets/fonts/OFL.txt](assets/fonts/OFL.txt).
