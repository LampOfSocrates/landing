"""Desktop launcher: "Landing Claude App" - a tkinter window with one labeled
section per pet project (vsal's media browser, the Datasette data table,
fingod, the landing page itself, a vsal terminal), plus a live log panel
underneath that records every button press and its outcome.

Run as `pythonw launcher.py` (what the Desktop shortcut does) so no console
window flashes. Install the shortcut with `python install.py`.

Moved here from video-saliency's `vsal/launcher.py` on 2026-08-26; the vsal
sections import vsal lazily so the window still opens without it installed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
import traceback
import webbrowser
from pathlib import Path

WINDOW_TITLE = "Landing Claude App"
LANDING_REPO = Path(__file__).resolve().parent.parent

# landing's dark palette (styles.css), so the window matches the site
BG = "#0e1116"
BG_SOFT = "#161a22"
FG = "#e8ecf3"
FG_SOFT = "#a3acbf"
ACCENT = "#7aa9ff"
ACCENT_WARM = "#ffb37a"
OK = "#6fd08c"
ERR = "#ff7a7a"


# ---------------------------------------------------------------- log panel

class LogPanel:
    """Read-only, timestamped, colour-tagged transcript of what the buttons did."""

    def __init__(self, parent):
        import tkinter as tk

        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="both", expand=True, padx=20, pady=(4, 8))

        header = tk.Frame(frame, bg=BG)
        header.pack(fill="x")
        tk.Label(header, text="LOG", font=("Segoe UI", 9, "bold"),
                 fg=FG_SOFT, bg=BG).pack(side="left")
        tk.Button(header, text="clear", font=("Segoe UI", 8), bg=BG_SOFT, fg=FG_SOFT,
                  relief="flat", command=self.clear).pack(side="right")

        body = tk.Frame(frame, bg=BG)
        body.pack(fill="both", expand=True, pady=(4, 0))
        scroll = tk.Scrollbar(body)
        scroll.pack(side="right", fill="y")
        self.text = tk.Text(body, height=12, width=86, wrap="word",
                            font=("Consolas", 9), bg=BG_SOFT, fg=FG_SOFT,
                            relief="flat", padx=10, pady=8,
                            yscrollcommand=scroll.set)
        self.text.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.text.yview)

        self.text.tag_config("time", foreground="#5c6478")
        self.text.tag_config("info", foreground=FG_SOFT)
        self.text.tag_config("action", foreground=ACCENT)
        self.text.tag_config("ok", foreground=OK)
        self.text.tag_config("warn", foreground=ACCENT_WARM)
        self.text.tag_config("err", foreground=ERR)
        self.text.config(state="disabled")

    def write(self, message: str, kind: str = "info") -> None:
        stamp = time.strftime("%H:%M:%S")
        self.text.config(state="normal")
        self.text.insert("end", f"{stamp}  ", "time")
        self.text.insert("end", f"{message}\n", kind)
        self.text.see("end")
        self.text.config(state="disabled")

    def clear(self) -> None:
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")
        self.write("log cleared")


# ------------------------------------------------------------- vsal sections
# vsal lives in its own repo and may not be importable; every entry point that
# needs it goes through here so a missing install is a log line, not a crash.

def _vsal(log):
    try:
        from vsal import browse, webui
    except ImportError as exc:
        log.write(f"vsal is not importable in this Python ({exc}) - "
                  "install it with `pip install -e ~/Code/2026/video-saliency`", "err")
        return None
    return browse, webui


def _ensure_web(log) -> bool:
    mods = _vsal(log)
    if not mods:
        return False
    _, webui = mods
    try:
        db = webui.resolve_db(None)
        webui.ensure_server(db)
    except (FileNotFoundError, RuntimeError) as exc:
        log.write(f"data table: {exc}", "err")
        return False
    log.write(f"data table: serving {db} at {webui.url()}", "ok")
    return True


def _start_web(log) -> None:
    _ensure_web(log)


def _open_web(log) -> None:
    mods = _vsal(log)
    if mods and _ensure_web(log):
        url = mods[1].url()
        webbrowser.open(url)
        log.write(f"data table: opened {url} in the browser", "ok")


def _restart_web(log) -> None:
    """Stop-then-start, e.g. to pick up a new catalog path or skin.

    Only ever touches the Datasette server on 8473 - the media browser on
    8474 has its own restart with its own command-line guard.
    """
    mods = _vsal(log)
    if not mods:
        return
    _, webui = mods
    try:
        webui.stop_server()
        log.write("data table: stopped the running server", "info")
    except RuntimeError as exc:
        log.write(f"data table: stop failed - {exc}", "err")
        return
    _ensure_web(log)


def _ensure_browse(log) -> bool:
    mods = _vsal(log)
    if not mods:
        return False
    browse, webui = mods
    try:
        db = webui.resolve_db(None)
        browse.ensure_server(db)
    except (FileNotFoundError, RuntimeError) as exc:
        log.write(f"media browser: {exc}", "err")
        return False
    log.write(f"media browser: serving {db} at {browse.url()}", "ok")
    return True


def _open_browse(log) -> None:
    mods = _vsal(log)
    if mods and _ensure_browse(log):
        url = mods[0].url()
        webbrowser.open(url)
        log.write(f"media browser: opened {url} in the browser", "ok")


def _restart_browse(log) -> None:
    mods = _vsal(log)
    if not mods:
        return
    browse, _ = mods
    try:
        browse.stop_server()
        log.write("media browser: stopped the running server", "info")
    except RuntimeError as exc:
        log.write(f"media browser: stop failed - {exc}", "err")
        return
    _ensure_browse(log)


# ----------------------------------------------------------------- fingod

FINGOD_REPO = Path.home() / "Code" / "2026" / "fingod"
FINGOD_PORT = 47816
FINGOD_URL = f"http://localhost:{FINGOD_PORT}"


def _fingod_running() -> bool:
    import urllib.error
    import urllib.request

    try:
        urllib.request.urlopen(FINGOD_URL, timeout=2)
    except urllib.error.HTTPError:
        return True  # any HTTP response means the server is up
    except OSError:
        return False
    return True


def _start_fingod(log, skip_backfill: bool = False) -> None:
    """run_local.ps1 backfills prices, backs up the DB, serves, opens the browser.

    -NoExit because the server is the LAST line of that script: without it a
    failure anywhere before it closes the console and takes the error with it,
    which reads as "restart did nothing".
    """
    script = FINGOD_REPO / "run_local.ps1"
    if not script.is_file():
        log.write(f"fingod: {script} not found", "err")
        return
    # Pin the interpreter: bare `python` in a fresh console may be a Python
    # without fingod's packages (the 3.14 install manager was first on PATH and
    # died on python-multipart). This launcher's own Python is known to have them.
    py = Path(sys.executable).with_name("python.exe")
    args = ["powershell", "-NoExit", "-ExecutionPolicy", "Bypass", "-File", str(script),
            "-Python", str(py)]
    if skip_backfill:
        args.append("-SkipBackfill")
    subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)
    if skip_backfill:
        log.write(f"fingod: launched {script.name} -SkipBackfill - serving now, "
                  "browser opens when ready", "ok")
    else:
        log.write(f"fingod: launched {script.name} in a new console - backfill runs "
                  "first, browser opens when ready", "warn")


def _open_fingod(log) -> None:
    if _fingod_running():
        webbrowser.open(FINGOD_URL)
        log.write(f"fingod: already running, opened {FINGOD_URL}", "ok")
    else:
        log.write("fingod: not responding, starting it", "info")
        _start_fingod(log)


def _restart_fingod(log) -> None:
    kill = (f"Get-NetTCPConnection -LocalPort {FINGOD_PORT} -State Listen -ErrorAction SilentlyContinue "
            "| Select-Object -ExpandProperty OwningProcess -Unique "
            "| ForEach-Object { Stop-Process -Id $_ -Force }")
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", kill],
                   capture_output=True, timeout=30)
    log.write(f"fingod: killed anything listening on {FINGOD_PORT}", "info")
    # Restart means "the server is wrong", not "the prices are stale": the
    # nightly scheduled task keeps those current, and a full backfill would put
    # a minute of price fetching between the click and a working page.
    _start_fingod(log, skip_backfill=True)


def _fingod_tasks(log) -> None:
    """A PowerShell window showing fingod's scheduled tasks and the timer log tail."""
    tail = FINGOD_REPO / "data" / "backfill_timer.log"
    cmd = (
        "Get-ScheduledTask -TaskName 'fingod*' | Format-Table TaskName, State -AutoSize; "
        "Get-ScheduledTask -TaskName 'fingod*' | Get-ScheduledTaskInfo | "
        "Format-List TaskName, LastRunTime, LastTaskResult, NextRunTime; "
        f"if (Test-Path '{tail}') {{ '--- backfill_timer.log (last 10) ---'; "
        f"Get-Content '{tail}' -Tail 10 }}"
    )
    subprocess.Popen(["powershell", "-NoExit", "-Command", cmd],
                     creationflags=subprocess.CREATE_NEW_CONSOLE)
    log.write("fingod: opened a console with scheduled tasks + timer log tail", "ok")


# ---------------------------------------------------------------- landing

def _open_landing(log) -> None:
    index = LANDING_REPO / "index.html"
    if not index.is_file():
        log.write(f"landing: {index} not found", "err")
        return
    webbrowser.open(index.as_uri())
    log.write(f"landing: opened {index}", "ok")


def _landing_folder(log) -> None:
    subprocess.Popen(["explorer", str(LANDING_REPO)])
    log.write(f"landing: opened {LANDING_REPO} in Explorer", "ok")


# ------------------------------------------------------------------- tools

def _open_cli(log) -> None:
    """Open a terminal ready to run vsal: Windows Terminal if present, else PowerShell."""
    if shutil.which("vsal"):
        banner = "vsal -h"
    else:
        py = str(Path(sys.executable).with_name("python.exe"))
        banner = f"& '{py}' -m vsal.cli -h"
    ps = ["powershell", "-NoExit", "-Command", banner]
    wt = shutil.which("wt")
    if wt:
        subprocess.Popen([wt, *ps])
        log.write(f"vsal cli: opened Windows Terminal running `{banner}`", "ok")
    else:
        subprocess.Popen(ps, creationflags=subprocess.CREATE_NEW_CONSOLE)
        log.write(f"vsal cli: opened PowerShell running `{banner}`", "ok")


SECTIONS = [
    ("MEDIA BROWSER", "browse footage with thumbnails (vsal, port 8474)", [
        ("open media browser", _open_browse),
        ("restart", _restart_browse),
    ]),
    ("DATA TABLE", "search/facet the catalog with Datasette (vsal, port 8473)", [
        ("start", _start_web),
        ("open", _open_web),
        ("restart", _restart_web),
    ]),
    ("FINGOD", f"market data + investment alerts ({FINGOD_URL})", [
        ("open fingod", _open_fingod),
        ("restart fingod", _restart_fingod),
        ("scheduled tasks", _fingod_tasks),
    ]),
    ("LANDING", "the ~/code/2026 portfolio page this app lives in", [
        ("open landing page", _open_landing),
        ("open repo folder", _landing_folder),
    ]),
    ("TOOLS", "a terminal ready to run vsal", [
        ("vsal cli", _open_cli),
    ]),
]


# -------------------------------------------------------------------- main

def main() -> None:
    import tkinter as tk

    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.configure(bg=BG)
    ico = Path(__file__).with_name("landing-claude-app.ico")
    if ico.is_file():
        try:
            root.iconbitmap(str(ico))
        except tk.TclError:
            pass

    body = tk.Frame(root, bg=BG)
    body.pack(fill="x")

    holder = {}

    def logged(label, fn):
        """Every button announces itself first, so the log shows intent then outcome."""
        def run():
            log = holder["log"]
            log.write(f"> {label}", "action")
            try:
                fn(log)
            except Exception:
                log.write(traceback.format_exc().strip().splitlines()[-1], "err")
        return run

    for i, (header, desc, buttons) in enumerate(SECTIONS):
        tk.Label(body, text=header, font=("Segoe UI", 9, "bold"), fg=ACCENT, bg=BG,
                 ).pack(anchor="w", padx=28, pady=(20 if i == 0 else 14, 0))
        tk.Label(body, text=desc, font=("Segoe UI", 9), fg=FG_SOFT, bg=BG,
                 ).pack(anchor="w", padx=28)
        row = tk.Frame(body, bg=BG)
        row.pack(anchor="w", padx=28, pady=(6, 0))
        for label, fn in buttons:
            tk.Button(row, text=label, font=("Segoe UI", 11), height=1,
                      bg=BG_SOFT, fg=FG, activebackground=ACCENT,
                      activeforeground=BG, relief="flat",
                      command=logged(label, fn),
                      ).pack(side="left", padx=(0, 8), ipadx=8, ipady=2)

    tk.Frame(root, bg="#252a35", height=1).pack(fill="x", padx=20, pady=(18, 0))
    holder["log"] = LogPanel(root)
    holder["log"].write(f"{WINDOW_TITLE} ready - {LANDING_REPO}", "info")
    root.mainloop()


if __name__ == "__main__":
    main()
