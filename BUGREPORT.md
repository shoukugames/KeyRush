# Reporting a bug in Key Rush

Found something wrong? Please tell us. Reports from young players and their parents are very welcome.

- **Email:** info@shoukugames.org
- **Website:** <https://shoukugames.org/>

## If the game crashed

The game saves the details to a file named `crash.log`. Please attach it to your report.

| System | Location |
|---|---|
| Linux | `~/.local/share/keyrush/crash.log` |
| Windows | `%APPDATA%\KeyRush\crash.log` (paste this into the File Explorer address bar) |

## Bug report form

Copy this into your email and fill in what you can.

```text
Game version:      (Credits screen, for example v0.1.0)
Installed from:    (.deb / Windows .exe / source)
Operating system:  (for example Ubuntu 24.04, or Windows 11)
Difficulty:        (Easy / Medium / Hard)
Round:             (for example Round 5)
Keyboard layout:   (for example US QWERTY, UK, German QWERTZ)

What happened:

What you expected to happen:

Steps to make it happen again:
1.
2.
3.

Does it happen every time?   (always / sometimes / once)

Crash log or screenshot:     (attach if you have one)
```

## Known issues

| Issue | Workaround |
|---|---|
| The `.deb` needs glibc 2.36 or newer (Debian 12, Ubuntu 23.04 or later). | On older systems, run from source (see the README). |
| The Windows `.exe` is unsigned, so SmartScreen may warn about it. | Choose **More info**, then **Run anyway**. |
| The Windows `.exe` is built and tested under Wine, and has not yet been run on a real Windows PC. | Please report any Windows-only problem. |
| The Windows `.exe` has no console, so `--version` prints nothing. | The version is on the Credits screen. |
| Sound and music are checked by automated tests, not yet by listening on real speakers. | Please tell us about any sound that seems wrong or too loud. |
| The game listens for the letters A S D F G H J K L ;. On AZERTY, QWERTZ (the ; key), Dvorak and other layouts, some of those letters aren't on the home row. | Switch to a US or UK QWERTY layout while playing. |
| The music takes a few seconds to start the first time the title screen opens, while the instruments are built. | None needed. It starts on its own. |

## Reset saved data

If a saved file is damaged, the game renames it with `.corrupt` on the end and starts a fresh one.
To start completely fresh, delete the data folder above.
To clear only the parents' statistics, press **Del** on the For Parents screen. This keeps the Top 10 tables.
