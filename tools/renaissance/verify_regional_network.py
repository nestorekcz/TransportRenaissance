"""Matching regional build loopback smoke test and old-fork rejection. GPL-2.0-only.

Run with normal Windows font/network access; launches isolated native windows.
This verifies a short session, not long-duration or cross-platform determinism.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time
from verify_regional import stage


def start(runtime, args, name):
    out = (runtime / f"{name}-stdout.log").open("w")
    err = (runtime / f"{name}-stderr.log").open("w")
    p = subprocess.Popen([str(runtime / "openttd.exe"), "-X", "-x", "-c", "openttd.cfg", "-d", "net=3", *args],
                         cwd=runtime, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True)
    return p, out, err


def main(root, seconds, incompatible_runtime):
    if not (incompatible_runtime / "openttd.exe").is_file():
        raise RuntimeError("Provide --incompatible-runtime pointing to an upstream or pre-regional game runtime")
    output = root / "artifacts/regional-verification/network"
    runtimes = {}
    for name in ("server", "matching", "old-fork"):
        target = output / name
        stage(root, target)
        (target / "scripts/autoexec.scr").write_text("")
        (target / "scripts/game_start.scr").write_text("")
        with (target / "openttd.cfg").open("a") as cfg:
            cfg.write(f'\n[network]\nserver_game_type = 0\nserver_name = "Regional Loopback Test"\nclient_name = "Regional {name}"\n')
        runtimes[name] = target
    # Previous executable and matching language catalog, deliberately without rg1 marker.
    shutil.copy2(incompatible_runtime / "openttd.exe", runtimes["old-fork"] / "openttd.exe")
    shutil.copytree(incompatible_runtime / "lang", runtimes["old-fork"] / "lang", dirs_exist_ok=True)
    (runtimes["matching"] / "scripts/on_client.scr").write_text("")
    save = root / "artifacts/regional-verification/run-0/save/regional-builder.sav"
    server, so, se = start(runtimes["server"], ["-D", "127.0.0.1:39793", "-g", str(save)], "server")
    try:
        time.sleep(2)
        if server.poll() is not None:
            raise RuntimeError("Regional dedicated server exited")
        server.stdin.write("unpause\nregional audit\n"); server.stdin.flush()
        for name, duration in (("matching", seconds), ("old-fork", 4)):
            company = 1 if name == "matching" else 255
            client, co, ce = start(runtimes[name], ["-v", "win32", "-s", "null", "-m", "null", "-n", f"127.0.0.1:39793#{company}"], name)
            try:
                if name == "matching":
                    time.sleep(3)
                    server.stdin.write("regional netverify 1691\n"); server.stdin.flush()
                    time.sleep(max(0, duration - 3))
                else:
                    time.sleep(duration)
                server.stdin.write("clients\nregional audit\nregional inspect 1691\n"); server.stdin.flush()
                time.sleep(0.2)
            finally:
                if client.poll() is None:
                    client.terminate()
                client.wait(timeout=10)
                co.close(); ce.close()
        server.stdin.write("quit\n"); server.stdin.flush()
        server.wait(timeout=15)
    finally:
        if server.poll() is None:
            server.terminate(); server.wait(timeout=10)
        so.close(); se.close()
    server_log = (runtimes["server"] / "server-stdout.log").read_text(encoding="utf-8", errors="replace")
    client_log = (runtimes["matching"] / "matching-stderr.log").read_text(encoding="utf-8", errors="replace")
    assert "name: 'Regional matching'" in server_log, server_log
    assert "wrong revision" in server_log, server_log
    assert "desync" not in client_log.lower(), client_log
    assert "/ 512 waiting for collection" in server_log, "Serialized storage-upgrade command did not execute"
    report = {"matching_session_seconds": seconds, "matching_client_active": True,
              "old_fork_rejected": True, "desync_reported": False, "serialized_storage_upgrade_executed": True,
              "scope": "One Windows loopback client; no adverse latency or cross-platform coverage."}
    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--seconds", type=int, default=65)
    parser.add_argument("--incompatible-runtime", type=Path, required=True,
                        help="Existing upstream or pre-regional runtime, including exe and matching lang directory")
    args = parser.parse_args()
    main(args.workspace.resolve(), args.seconds, args.incompatible_runtime.resolve())
