## What this is
The portfolio landing page for `~/code/2026` — a static HTML/CSS/JS site listing pet projects as cards, with live GitHub commit badges and a "Latest activity" summary grid.

## Where it runs
Static site, no build step. Deployed via GitHub Pages/similar under LampOfSocrates; commit badges fetch live from the GitHub API client-side (cached 30 min in localStorage).

## Features
- Project card grid (17 cards) with sort (Recent/Name) and view (Cards/List) toggles
- Live "Updated X ago · N commits" badges per card via GitHub API, with localStorage caching and stale-while-revalidate fallback
- Dark/light theme toggle, persisted
- Hand-authored "Latest activity" summary grid at the top, refreshed periodically from each project's own status

## Recently tried
- 2026-08-16: Refreshed the "Latest activity" grid from each project's own LATEST.md (What this is / Recently tried), added this LATEST.md.
- 2026-08-10: Added cupel project card; refreshed latest-activity entry from skein to cupel.
- 2026-08-10: Renamed loom to skein in latest activity; refreshed status and date.
- 2026-08-02: Added Latest activity grid at top: DIRT, loom, afterglow, landing, llmeval, video-saliency.
- 2026-07-16: Removed dead AWS live links (fingod, google-adk-sample, cine_nova) after those projects went local-first.

## Next
- Seven sibling projects have no card yet (afterglow, DIRT, agy-cupel, claude-cupel, codex-cupel, downbeat, journey-replayer) — most are early-stage/spec-only, worth a lighter-weight card treatment.
- The "Latest activity" grid is still hand-authored per update; could script it to regenerate from each repo's LATEST.md instead (inferred — no such tooling exists yet).
- No automated commit-data fetch for repos without a GitHub remote (agy-cupel, claude-cupel, codex-cupel, propertyguru aren't pushed anywhere).
