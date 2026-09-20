"""Put a "Landing Claude App" shortcut on the Desktop (and remove the old
"My Claude Apps" one this app was moved from).

    python install.py            # install, tidy up the old shortcut
    python install.py --dry-run  # print the spec + PowerShell, touch nothing
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SHORTCUT_NAME = "Landing Claude App.lnk"
OLD_SHORTCUT_NAME = "My Claude Apps.lnk"  # what vsal's launcher used to install
ICON_NAME = "landing-claude-app.ico"


def _pythonw() -> str:
    """Prefer pythonw.exe so the launcher opens with no console flash."""
    w = Path(sys.executable).with_name("pythonw.exe")
    return str(w) if w.is_file() else sys.executable


def icon_path() -> Path:
    return APP_DIR / ICON_NAME


def write_icon(path: Path | None = None) -> Path:
    """Draw the icon with Pillow: landing's blue card-grid on its dark ground."""
    from PIL import Image, ImageDraw

    path = path or icon_path()
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, 248, 248), radius=52, fill=(14, 17, 22, 255),
                        outline=(122, 169, 255, 255), width=12)
    for x0, y0 in ((72, 72), (140, 72), (72, 140), (140, 140)):
        d.rounded_rectangle((x0, y0, x0 + 44, y0 + 44), radius=10,
                            fill=(122, 169, 255, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    return path


def shortcut_spec() -> dict:
    """What the Desktop shortcut should point at (separate from creating it,
    so this can be checked without touching the real Desktop)."""
    return {
        "name": SHORTCUT_NAME,
        "target": _pythonw(),
        "arguments": f'"{APP_DIR / "launcher.py"}"',
        "icon": str(icon_path()),
        "workdir": str(APP_DIR),
    }


def _q(s) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def shortcut_ps_script(spec: dict, remove_old: str | None = OLD_SHORTCUT_NAME) -> str:
    """PowerShell that drops the .lnk on the Desktop via WScript.Shell COM.

    GetFolderPath('Desktop') follows OneDrive-redirected desktops, which a
    hardcoded %USERPROFILE%\\Desktop would miss.
    """
    lines = [
        "$d = [Environment]::GetFolderPath('Desktop')",
        f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d {_q(spec['name'])}))",
        f"$s.TargetPath = {_q(spec['target'])}",
        f"$s.Arguments = {_q(spec['arguments'])}",
        f"$s.IconLocation = {_q(spec['icon'])}",
        f"$s.WorkingDirectory = {_q(spec['workdir'])}",
        "$s.Save()",
    ]
    if remove_old:
        lines.append(
            f"$old = Join-Path $d {_q(remove_old)}; "
            "if (Test-Path $old) { Remove-Item $old -Force; \"removed $old\" }")
    return "; ".join(lines)


def install_shortcut() -> dict:
    """Create the icon and the Desktop shortcut. Returns the spec used."""
    spec = shortcut_spec()
    write_icon(Path(spec["icon"]))
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", shortcut_ps_script(spec)],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            (result.stderr or result.stdout).strip()[:500] or "shortcut creation failed")
    if result.stdout.strip():
        print(result.stdout.strip())
    return spec


if __name__ == "__main__":
    spec = shortcut_spec()
    if "--dry-run" in sys.argv:
        for k, v in spec.items():
            print(f"{k:10} {v}")
        print("\n" + shortcut_ps_script(spec))
    else:
        install_shortcut()
        print(f"Desktop shortcut created: {spec['name']} -> {spec['target']} {spec['arguments']}")
        if not spec["target"].lower().endswith("pythonw.exe"):
            print("warning: pythonw.exe not found next to your Python - "
                  "the launcher will flash a console window")
