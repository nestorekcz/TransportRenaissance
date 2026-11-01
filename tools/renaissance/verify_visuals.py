"""Capture real native game zoom/fallback/save-reload fixtures. GPL-2.0-only."""
from pathlib import Path
import shutil
import subprocess
import time

WORKSPACE = Path(__file__).resolve().parents[3]
ARTIFACTS = WORKSPACE / "artifacts"
EVIDENCE = ARTIFACTS / "evidence"
EVIDENCE.mkdir(exist_ok=True)

for name, origin, zoom, blitter in (
    ("baseline-detail", "baseline", 1, "32bpp-anim"),
    ("after-detail", "fork", 1, "32bpp-anim"),
    ("after-4x", "fork", 0, "32bpp-anim"),
    ("after-normal", "fork", 2, "32bpp-anim"),
    ("after-indexed", "fork", 2, "8bpp-optimized"),
):
    source = ARTIFACTS / f"{origin}-runtime"
    target = ARTIFACTS / "visual-verification" / name
    target.mkdir(parents=True, exist_ok=True)
    for folder in ("baseset", "newgrf", "lang", "game"):
        if (source / folder).exists():
            shutil.copytree(source / folder, target / folder, dirs_exist_ok=True)
    for file in ("openttd.exe", "libunwind.dll"):
        shutil.copy2(source / file, target / file)
    config = (source / "openttd.cfg").read_text(encoding="utf-8-sig").replace('blitter = "32bpp-anim"', f'blitter = "{blitter}"')
    (target / "openttd.cfg").write_text(config)
    (target / "scripts").mkdir(exist_ok=True)
    (target / "scripts/game_start.scr").write_text(f"zoomto {zoom}\nscrollto instant 50 43\nscreenshot viewport no_con {name}\n")
    # Loading the fork's actual saved result checks round-trip compatibility.
    scene = ARTIFACTS / "fork-runtime/save/renaissance-fork-reload.sav" if origin == "fork" else source / "save/renaissance-coast.sav"
    with (target / "stdout.log").open("w") as stdout, (target / "stderr.log").open("w") as stderr:
        process = subprocess.Popen([str(target / "openttd.exe"), "-X", "-x", "-c", "openttd.cfg", "-g", str(scene)], cwd=target, stdout=stdout, stderr=stderr)
        try:
            for _ in range(100):
                capture = target / "screenshot" / f"{name}.png"
                if capture.exists():
                    time.sleep(0.5)
                    shutil.copy2(capture, EVIDENCE / capture.name)
                    print(f"Captured {name}; process alive={process.poll() is None}", flush=True)
                    break
                if process.poll() is not None:
                    raise RuntimeError(f"Game exited before capture: {target}")
                time.sleep(0.1)
            else:
                raise RuntimeError(f"No capture: {target}")
        finally:
            process.terminate(); process.wait(timeout=10)
