"""Capture the real native planner and example map. GPL-2.0-only."""
from pathlib import Path
import subprocess
import time
from verify_regional import stage


def main():
    root = Path(__file__).resolve().parents[3]
    for name, script in (("regional-inspector", "zoomto 1\nscrollto instant 53 14\nregional view 1724\nscreenshot viewport no_con regional-inspector\n"),
                         ("regional-town", "zoomto 2\nscrollto instant 47 14\nscreenshot viewport no_con regional-town\n")):
        target = root / "artifacts/regional-verification/visual" / name
        stage(root, target)
        (target / "scripts/autoexec.scr").write_text("")
        (target / "scripts/game_start.scr").write_text("pause\n" + script)
        screenshot = target / "screenshot" / f"{name}.png"
        if screenshot.exists():
            screenshot.unlink()
        with (target / "stdout.log").open("w") as out, (target / "stderr.log").open("w") as err:
            p = subprocess.Popen([str(target / "openttd.exe"), "-X", "-x", "-c", "openttd.cfg", "-g",
                                  str(root / "artifacts/regional-verification/run-0/save/regional-builder.sav"), "-s", "null", "-m", "null"],
                                 cwd=target, stdout=out, stderr=err)
            try:
                for _ in range(150):
                    if screenshot.exists():
                        time.sleep(0.5)
                        print(screenshot)
                        break
                    if p.poll() is not None:
                        raise RuntimeError("Native game exited before screenshot")
                    time.sleep(0.1)
                else:
                    raise RuntimeError("Screenshot timed out")
            finally:
                if p.poll() is None:
                    p.terminate(); p.wait(timeout=10)


if __name__ == "__main__":
    main()
