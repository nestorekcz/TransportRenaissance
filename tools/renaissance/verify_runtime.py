"""Repeatable isolated native runtime probes. GPL-2.0-only.

GUI mode measures a fixed calendar interval with OpenTTD's built-in profiler.
Null mode measures 10000 simulation-loop iterations, including startup/exit.
Do not interpret null wall time as rendered frame time.
"""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import shutil
import subprocess
import time


class MemoryCounters(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
            "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
            "PagefileUsage", "PeakPagefileUsage")]


def probe(source, output, name, mode, scene, index):
    run = output / f"{name}-{mode}-{index}"
    run.mkdir(parents=True, exist_ok=True)
    for directory in ("baseset", "lang", "newgrf", "game"):
        if (source / directory).exists():
            shutil.copytree(source / directory, run / directory, dirs_exist_ok=True)
    for file in ("openttd.exe", "libunwind.dll", "openttd.cfg"):
        shutil.copy2(source / file, run / file)
    (run / "scripts").mkdir(exist_ok=True)
    start = "zoomto 3\nscrollto instant 50 43\nunpause\n"
    if mode == "gui":
        start += "schedule on-next-calendar-month scripts/measure.scr\n"
        (run / "scripts/measure.scr").write_text("script metrics.log\nfps\nscript\nquit\n")
    (run / "scripts/game_start.scr").write_text(start)
    command = [str(run / "openttd.exe"), "-X", "-x", "-c", "openttd.cfg", "-g", str(scene)]
    if mode == "null":
        command += ["-v", "null:ticks=10000", "-s", "null", "-m", "null"]
    peak = 0
    begin = time.perf_counter()
    with (run / "stdout.log").open("w") as stdout, (run / "stderr.log").open("w") as stderr:
        process = subprocess.Popen(command, cwd=run, stdout=stdout, stderr=stderr)
        while process.poll() is None:
            counters = MemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            if ctypes.windll.psapi.GetProcessMemoryInfo(wintypes.HANDLE(process._handle), ctypes.byref(counters), counters.cb):
                peak = max(peak, counters.PeakWorkingSetSize)
            if time.perf_counter() - begin > 150:
                process.terminate()
                raise RuntimeError(f"Probe timed out: {run}")
            time.sleep(0.1)
    result = {"name": name, "mode": mode, "repeat": index, "exit_code": process.returncode,
              "wall_seconds": round(time.perf_counter() - begin, 3), "peak_working_set_bytes": peak,
              "scene": str(scene), "metrics": (run / "metrics.log").read_text() if (run / "metrics.log").exists() else None}
    print(json.dumps(result), flush=True)
    if process.returncode != 0:
        raise RuntimeError(f"Probe failed: {run}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--fork", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("gui", "null"), default="null")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--scene", type=Path, help="Optional shared busy-save workload")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    scene = args.scene.resolve() if args.scene else args.baseline.resolve() / "save/renaissance-coast.sav"
    results = []
    for index in range(args.repeats):
        for name, source in (("baseline", args.baseline.resolve()), ("fork", args.fork.resolve())):
            results.append(probe(source, output, name, args.mode, scene, index))
            (output / f"{args.mode}-results.json").write_text(json.dumps(results, indent=2) + "\n")
