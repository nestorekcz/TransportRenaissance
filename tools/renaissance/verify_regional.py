"""Build a real native regional example; verify freight, saves and reproducibility.

Run after building the fork, with normal Windows font access. No cargo is seeded.
GPL-2.0-only.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from PIL import Image


def stage(root, target):
    target.mkdir(parents=True, exist_ok=True)
    source = root / "artifacts/fork-runtime"
    for folder in ("baseset", "newgrf"):
        shutil.copytree(source / folder, target / folder, dirs_exist_ok=True)
    shutil.copytree(root / "artifacts/fork-build/lang", target / "lang", dirs_exist_ok=True)
    shutil.copy2(root / "artifacts/fork-build/openttd.exe", target / "openttd.exe")
    for filename in ("libunwind.dll", "libc++.dll", "libwinpthread-1.dll"):
        if (source / filename).exists():
            shutil.copy2(source / filename, target / filename)
    for folder in ("scripts", "save", "scenario/heightmap"):
        (target / folder).mkdir(parents=True, exist_ok=True)
    Image.new("L", (128, 128), 160).save(target / "scenario/heightmap/regional-flat.png")
    config = (root / "TransportRenaissance/media/renaissance/demo/openttd.cfg").read_text(encoding="utf-8").split("[game_scripts]")[0]
    config = config.replace("town_growth_rate = 0", "town_growth_rate = 2")
    config = config.replace("regional_mode = 0", "regional_mode = 1")
    config = config.replace("starting_year = 1950", "starting_year = 1960")
    config = config.replace("vehicle_breakdowns = 0", "vehicle_breakdowns = 0\ndisasters = false")
    (target / "openttd.cfg").write_text(config + "\n[newgrf-static]\nrenaissance-meadow.grf =\n", encoding="utf-8")


def run(target, args=()):
    start = time.perf_counter()
    with (target / "stdout.log").open("w") as out, (target / "stderr.log").open("w") as err:
        result = subprocess.run([str(target / "openttd.exe"), "-X", "-x", "-c", "openttd.cfg", "-G", "20261101",
                                 "-v", "null:ticks=100000", "-s", "null", "-m", "null", *args],
                                cwd=target, stdout=out, stderr=err, timeout=120)
    assert result.returncode == 0, (target, result.returncode)
    stderr = (target / "stderr.log").read_text(encoding="utf-8", errors="replace")
    assert not any(word in stderr.lower() for word in ("assertion", "corrupt", "backed-up", "fatal")), stderr
    return round(time.perf_counter() - start, 4)


def audits(text):
    return [dict((k, int(v)) for k, v in re.findall(r"(\w+)=(\d+)", line))
            for line in text.splitlines() if line.startswith("REGIONAL_AUDIT")]


def stress(root, output):
    target = output / "stress"
    stage(root, target)
    config = target / "openttd.cfg"
    config.write_text(config.read_text(encoding="utf-8").replace("regional_mode = 1", "regional_mode = 2"), encoding="utf-8")
    (target / "stress.log").write_text("")
    (target / "scripts/autoexec.scr").write_text("load_heightmap regional-flat.png\n")
    (target / "scripts/game_start.scr").write_text("script stress.log\nregional demo\nregional stress\nunpause\nschedule on-next-calendar-month scripts/month00.scr\n")
    for month in range(36):
        script = "regional audit\n"
        script += "regional status\nsave regional-stress\nscript\nquit\n" if month == 35 else f"schedule on-next-calendar-month scripts/month{month+1:02}.scr\n"
        (target / f"scripts/month{month:02}.scr").write_text(script)
    seconds = run(target)
    log = (target / "stress.log").read_text(encoding="utf-8")
    rows = audits(log)
    assert "REGIONAL_STRESS_READY lots=1000" in log, log[:2000]
    assert len(rows) == 36 and all(row["inventory_errors"] == 0 for row in rows)
    assert rows[-1]["population"] > 10000
    result = {"map": "128 x 128", "lots": 1000, "months": 36,
              "wall_seconds_startup_construction_simulation_save_exit": seconds, "final": rows[-1]}
    (target / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main(root):
    output = root / "artifacts/regional-verification"
    results = []
    trajectories = []
    for repeat in range(2):
        target = output / f"run-{repeat}"
        stage(root, target)
        (target / "demo.log").write_text("")
        (target / "scripts/autoexec.scr").write_text("load_heightmap regional-flat.png\n")
        (target / "scripts/game_start.scr").write_text("script demo.log\nregional demo\nunpause\nschedule on-next-calendar-month scripts/month00.scr\n")
        for month in range(24):
            script = "regional audit\n"
            if month == 23:
                script += "regional status\nsave regional-builder\nscript\nquit\n"
            else:
                script += f"schedule on-next-calendar-month scripts/month{month+1:02}.scr\n"
            (target / f"scripts/month{month:02}.scr").write_text(script)
        seconds = run(target)
        log = (target / "demo.log").read_text(encoding="utf-8")
        assert "REGIONAL_DEMO_READY" in log and "DEMO command failed" not in log, log
        samples = audits(log)
        assert len(samples) == 24, samples
        final = samples[-1]
        assert final["lots"] == 16 and final["vehicles"] == 4
        assert final["population"] > 0 and final["produce_delivered"] > 0 and final["food_delivered"] > 0
        assert all(s["inventory_errors"] == 0 for s in samples)
        trajectories.append(samples)
        results.append({"repeat": repeat, "wall_seconds_including_startup_save_exit": seconds, "final": final})
    assert trajectories[0] == trajectories[1], "Identically seeded native worlds diverged"
    source = output / "run-0"
    reload = output / "reload"
    stage(root, reload)
    config = reload / "openttd.cfg"
    config.write_text(config.read_text(encoding="utf-8").replace("regional_mode = 1", "regional_mode = 0"), encoding="utf-8")
    (reload / "scripts/autoexec.scr").write_text("")
    (reload / "reload.log").write_text("")
    (reload / "scripts/game_start.scr").write_text("script reload.log\nregional audit\nregional status\nsave roundtrip\nscript\nquit\n")
    run(reload, ("-g", str(source / "save/regional-builder.sav")))
    loaded = audits((reload / "reload.log").read_text(encoding="utf-8"))[0]
    assert loaded == trajectories[0][-1], ("Save roundtrip mismatch", loaded, trajectories[0][-1])
    legacy = output / "legacy"
    stage(root, legacy)
    (legacy / "scripts/autoexec.scr").write_text("")
    (legacy / "legacy.log").write_text("")
    (legacy / "scripts/game_start.scr").write_text("script legacy.log\nregional audit\nregional status\nscript\nquit\n")
    run(legacy, ("-g", str(root / "TransportRenaissance/media/renaissance/demo/renaissance-coast.sav")))
    legacy_log = (legacy / "legacy.log").read_text(encoding="utf-8")
    assert "TRANSPORT CLASSIC" in legacy_log and audits(legacy_log)[0]["lots"] == 0
    classic = output / "classic-new-world"
    stage(root, classic)
    config = classic / "openttd.cfg"
    normal_config = (root / "TransportRenaissance/media/renaissance/openttd.cfg").read_text(encoding="utf-8")
    normal_config = normal_config.replace("map_x = 8", "map_x = 7").replace("map_y = 8", "map_y = 7")
    config.write_text(normal_config + "\n[newgrf-static]\nrenaissance-meadow.grf =\n", encoding="utf-8")
    (classic / "scripts/autoexec.scr").write_text("load_heightmap regional-flat.png\n")
    (classic / "classic.log").write_text("")
    (classic / "scripts/game_start.scr").write_text("script classic.log\nregional demo\nregional status\nregional audit\nscript\nquit\n")
    run(classic)
    classic_log = (classic / "classic.log").read_text(encoding="utf-8")
    assert "TRANSPORT CLASSIC" in classic_log and audits(classic_log)[0]["lots"] == 0, classic_log
    assert "REGIONAL_DEMO_READY" not in classic_log, classic_log
    checks = output / "command-checks"
    stage(root, checks)
    (checks / "scripts/autoexec.scr").write_text("")
    (checks / "checks.log").write_text("")
    (checks / "scripts/game_start.scr").write_text("script checks.log\nregional verify\nscript\nquit\n")
    run(checks, ("-g", str(source / "save/regional-builder.sav")))
    check_log = (checks / "checks.log").read_text(encoding="utf-8")
    assert "REGIONAL_CHECKS_OK count=20" in check_log and "REGIONAL_CHECK FAIL" not in check_log, check_log
    report = {"seed": 20261101, "map": "128 x 128 flat temperate", "cycles": "24 calendar months, native vehicle simulation",
              "runs": results, "identical_seeded_trajectories": True, "save_roundtrip_exact_audit": True,
              "version_362_save_migrated_to_classic": True, "cargo_seeded": 0,
              "classic_new_world_opt_out": True,
              "mode_selectable_before_creation_and_live_change_rejected": True,
              "builder_save_restores_mode_when_config_is_classic": True,
              "native_command_and_utility_checks": 20, "stress": stress(root, output),
              "scope": "Null driver timings include startup/save/exit and do not measure renderer frame time."}
    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[3])
    main(parser.parse_args().workspace.resolve())
