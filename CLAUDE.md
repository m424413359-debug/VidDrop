# VidDrop — project notes for Claude

VidDrop is a desktop GUI (Python + CustomTkinter) for **yt-dlp**, built by Ahmed Al-Nahhal
(GitHub: `m424413359-debug`). Users paste a link, pick quality / subtitles, and downloads run in a queue.
Ahmed is a CS student in Gaza; talk to him in Arabic (Palestinian dialect is fine), keep technical terms in English.

## Files
- `viddrop.py` — the whole app (single file)
- `requirements.txt` — `yt-dlp[default]`, `customtkinter`, `pillow`, `imageio-ffmpeg`
- `setup.bat` / `run.bat` / `run_debug.bat` / `update.bat` — Windows helpers for running from source
- `build_exe.bat` + `make_icon.py` — local PyInstaller build (kept for local builds)
- `.github/workflows/release.yml` — builds `VidDrop.exe` on windows-latest, runs `.github/scripts/test_windows.py`
  (exe starts; update download → swap while running → relaunch), then publishes the Release (see Release process)
- `CHANGELOG.txt` — one entry per version (Arabic)

## Working rules (agreed with Ahmed — follow strictly)
1. **Discuss before doing.** Explain the plan for a change and wait for his approval before writing code.
2. **One change per version.** Each version gets a tag (`v1.1`, `v1.2`, …) and a CHANGELOG entry.
3. **He tests on his Windows laptop** (Core i3, 8 GB RAM, slow internet) before the next version starts.
4. Don't refactor or "improve" things outside the agreed change.
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

## Next: v1.3 — weekly scheduled build when a new yt-dlp is released (agreed: separate version after v1.2 works)

## Later (roadmap, one per version, order to be confirmed)
Speed limit + scheduled downloads · download library/history · playlist download with selection ·
in-app search · audio bitrate / M4A · embed MP3 cover & metadata · parallel downloads · tray + notifications.
Android APK is **postponed** (CustomTkinter doesn't run on Android; YouTube on Android needs a JS runtime —
consider a Flet prototype later).
