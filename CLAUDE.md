# VidDrop — project notes for Claude

VidDrop is a desktop GUI (Python + CustomTkinter) for **yt-dlp**, built by Ahmed Al-Nahhal
(GitHub: `m424413359-debug`). Users paste a link, pick quality / subtitles, and downloads run in a queue.
Ahmed is a CS student in Gaza; talk to him in Arabic (Palestinian dialect is fine), keep technical terms in English.

## Files
- `viddrop.py` — the whole app (single file)
- `requirements.txt` — `yt-dlp[default]`, `customtkinter`, `pillow`, `imageio-ffmpeg`
- `setup.bat` / `run.bat` / `run_debug.bat` / `update.bat` — Windows helpers for running from source
- `build_exe.bat` + `make_icon.py` — local PyInstaller build (kept for local builds)
- `.github/workflows/release.yml` — builds `VidDrop.exe` on windows-latest, tests it, publishes the Release
  (see Release process). Its scripts live in `.github/scripts/`:
  - `plan_release.py` — decides build / publish / weekly yt-dlp bump
  - `test_windows.py` — self-test inside the exe, first run (Deno auto-download), single instance,
    update download → swap while running → relaunch, and no `error.log`
  - `release_notes.py` — CHANGELOG entry + "how to run" footer + the bundled `yt-dlp X` line
- `.gitattributes` — `* -text`: files are byte-exact everywhere (`.bat`/`.txt` are CRLF, the rest LF). Keep it that way.
- `CHANGELOG.txt` — one entry per version (Arabic)

## Working rules (agreed with Ahmed — follow strictly)
1. **Discuss before doing.** Explain the plan for a change and wait for his approval before writing code.
   (He may then say "finish it without coming back" — that covers PR, merge and release for that plan only.)
2. A version may contain several changes (Ahmed dropped the old "one change per version" rule on 2026-11-15).
   Each version still gets a CHANGELOG entry.
3. **He tests on his Windows laptop** (Core i3, 8 GB RAM, slow internet).
4. Don't refactor or "improve" things outside the agreed plan.
5. Be honest about what was and wasn't tested.

## Version history
- **v1.0** — original app.
- **v1.1** — single progress bar for video+audio with phase labels (الفيديو 1/2، الصوت 2/2);
  confirm dialog when removing an unfinished download; cancelling deletes all its downloaded files;
  removing a *finished* item keeps the file on disk.
  (Background: YouTube sends HD as separate video + audio. In v1.0 each part had its own bar, so Ahmed
  thought the audio part was a duplicate and cancelled it → videos without sound.)

- **v1.2** — in-app updates, released automatically from `main`. Details below.

## Release process
- Repo is **public** (`m424413359-debug/VidDrop`), default branch `main`.
- Claude's cloud session can push only its own branch — **it cannot push tags**. So releases are automatic:
  when a push to `main` carries an `APP_VERSION` that has no Release yet, the workflow builds, tests,
  and creates the tag `vX.Y` + the Release itself. Nobody needs to push tags (pushing one still works).
- A new version = bump `APP_VERSION` + add a CHANGELOG entry (notes are taken from it) → PR → merge to `main`.
- Pull requests run the build + Windows tests without publishing — check them before merging.
- **Weekly (Monday 03:17 UTC):** if PyPI has a newer yt-dlp than the `yt-dlp X` line in the latest Release,
  the workflow bumps the patch number (1.3 → 1.3.1 → 1.3.2), adds a CHANGELOG line, builds, tests, commits the
  bump to `main` and publishes. So `main` can move on its own — always fetch before starting work, and take the
  next manual version from the current `APP_VERSION` (e.g. 1.3.2 → 1.4).

## v1.2 — in-app updates (as implemented)
- `APP_VERSION` constant, shown next to the app name.
- GitHub Actions: on tag `v*`, build `VidDrop.exe` (PyInstaller, windows-latest) and attach it to a GitHub Release
  with the CHANGELOG notes.
- On startup the app checks `releases/latest` (public repo, no token), shows an "update available" banner with notes,
  downloads the new exe with progress, swaps it via a small helper script after exit, and relaunches.
  Queue and settings (`~/.viddrop/`) must survive. Setting to turn auto-check off.
- Only self-update when running as a frozen exe; from source, just point to the Releases page.
- Download goes to `~/.viddrop/update/VidDrop-<ver>.exe(.part)` and resumes with HTTP Range after a cut.
- Swap: `update.bat` (written to `~/.viddrop/update/`) renames the running exe to `VidDrop.old.exe`, moves the new one
  in, starts it; the new version deletes `.old.exe` on startup. Child env is cleaned of PyInstaller vars.
- Ahmed chose: no "skip this version" button, no "check now" button.

## v1.3 — runs on any Windows 10/11 machine (as implemented)
- **Deno** (needed by yt-dlp for YouTube): not bundled (it is ~98 MB unpacked). On Windows, if `deno` is not on PATH
  and not in `~/.viddrop/bin/`, the app downloads it there on first run (41 MB zip, resumable, banner with progress)
  and passes it to yt-dlp via `js_runtimes`. Failure → warning banner with retry; details in `error.log`.
- **`VidDrop.exe --selftest report.json`**: checks FFmpeg, Deno, and downloads a local sample as video + MP3 through
  the real queue, in a temp config dir (never touches the user's `~/.viddrop`). CI runs it before every publish.
  A YouTube extraction is reported as info only (YouTube often blocks GitHub runners).
- `~/.viddrop/error.log` + a message box on a fatal error; Tk callback and thread exceptions are logged too.
- Single instance (Windows mutex); a second launch brings the open window to the front.
- Window size is clamped to the screen (small screens, 125%/150% scaling). PyInstaller `--splash` while unpacking.
- Self-update only when the exe's folder is writable; otherwise the banner opens the Releases page.
- Known limits (cannot fix in code): SmartScreen / antivirus warnings (unsigned exe — would need a code-signing
  certificate, e.g. SignPath's free OSS program), Windows 7/8 and 32-bit are unsupported.

## Later (roadmap, one per version, order to be confirmed)
Speed limit + scheduled downloads · download library/history · playlist download with selection ·
in-app search · audio bitrate / M4A · embed MP3 cover & metadata · parallel downloads · tray + notifications.
Android APK is **postponed** (CustomTkinter doesn't run on Android; YouTube on Android needs a JS runtime —
consider a Flet prototype later).
