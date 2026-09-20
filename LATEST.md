## What this is
The portfolio landing page for `~/code/2026` — a static HTML/CSS/JS site listing pet projects as cards, with live GitHub commit badges and a "Latest activity" summary grid.

## Where it runs
Static site, no build step. `app/` also holds "Landing Claude App", a tkinter
desktop launcher (`pythonw app/launcher.py`; `python app/install.py` puts the
shortcut on the Desktop). Deployed via GitHub Pages/similar under LampOfSocrates; commit badges fetch live from the GitHub API client-side (cached 30 min in localStorage).

## Features
- Project card grid (23 cards) with sort (Recent/Name) and view (Cards/List) toggles
- Live "Updated X ago · N commits" badges per card via GitHub API, with localStorage caching and stale-while-revalidate fallback
- Dark/light theme toggle, persisted
- Hand-authored "Latest activity" summary grid at the top, refreshed periodically from each project's own status
- `app/` desktop launcher: one section per project (vsal media browser/data table, fingod, landing, vsal cli) with a timestamped log panel underneath recording every button press and its outcome

## Recently tried
- 2026-09-20: itinmap got its first commit and a private GitHub repo, then a card here (`.card--itinmap`, `icons/itinmap.svg`, no `data-repo` because private); activity row moved to 09-20; project count 22 -> 23. Committed and pushed landing, including `app/` (launcher), which had been untracked since 08-26.
- 2026-09-20: Second audit pass, same day. No folders added or deleted since the first. Grid: fingod row moved 09-18 -> 09-20 (month of work pushed; 3 test failures open), added propertyguru and xai-starter rows. All 21 repos with a remote are fully pushed.
- 2026-09-20: Audited every sibling folder against this page. Removed agy-cupel/claude-cupel/codex-cupel (folders deleted) from the activity grid; rewrote the grid in plain English from each project's LATEST.md (fingod, clove-circle, cupel, video-saliency, hock, moneycompass refreshed; itinmap row added, no card yet). Pushed hock's 2 unpushed commits. Renamed downbeat -> onbeat here too (card, `icons/onbeat.svg`, `.card--onbeat`, activity row); onbeat is now on GitHub as a private repo, so no `data-repo`.
- 2026-09-18: "open fingod" failed with a python-multipart error: `run_local.ps1` used bare `python`, which in the spawned console was the 3.14 install manager (no fingod deps). Launcher now passes `-Python <its own sys.executable>` and the script probes for a working interpreter itself.
- 2026-08-26: Moved video-saliency's "My Claude Apps" launcher here as `app/` and renamed it "Landing Claude App"; added the log panel, landing's dark palette, a LANDING section, and lazy vsal imports so the window opens without vsal. Deleted `vsal/launcher.py` + `vsal install-launcher`; old Desktop shortcut removed by the installer.

## Next
- The "Latest activity" grid is still hand-authored per update; could script it to regenerate from each repo's LATEST.md instead (inferred — no such tooling exists yet).
- `propertyguru` and `llmeval` cards carry a `data-repo` for GitHub repos that don't exist, so their badge fetch 404s. No remote: llmeval (local git only); propertyguru (no git). hock, onbeat and itinmap are pushed but private, so they stay without `data-repo`.
