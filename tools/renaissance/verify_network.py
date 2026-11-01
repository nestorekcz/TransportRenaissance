"""Local matching-fork / upstream-rejection smoke test. GPL-2.0-only.

Uses only loopback and disposable runtime copies. Not a long-duration desync test.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time


def stage(source, target):
    target.mkdir(parents=True, exist_ok=True)
    for name in ("openttd.exe", "libunwind.dll", "openttd.cfg"):
        shutil.copy2(source / name, target / name)
    for name in ("baseset", "lang", "newgrf", "game", "save"):
        if (source / name).exists():
            shutil.copytree(source / name, target / name, dirs_exist_ok=True)
    # Do not allow any stored master-server advertisement setting.
    with (target / "openttd.cfg").open("a") as file:
        file.write(f'\n[network]\nserver_game_type = 0\nserver_name = "Renaissance Local Verification"\nclient_name = "Renaissance {target.name}"\n')
    return target


def start(runtime, args, name):
    stdout = (runtime / f"{name}-stdout.log").open("w")
    stderr = (runtime / f"{name}-stderr.log").open("w")
    process = subprocess.Popen([str(runtime / "openttd.exe"), "-X", "-x", "-c", "openttd.cfg", "-d", "net=3", *args],
                               cwd=runtime, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True)
    return process, stdout, stderr


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--seconds", type=int, default=30)
    args = parser.parse_args()
    artifacts = args.workspace.resolve() / "artifacts"
    output = artifacts / "network-verification"
    server_dir = stage(artifacts / "fork-dedicated-runtime", output / "server")
    fork_dir = stage(artifacts / "fork-runtime", output / "fork-client")
    baseline_dir = stage(artifacts / "baseline-runtime", output / "upstream-client")
    server, out, err = start(server_dir, ["-D", "127.0.0.1:39791", "-g", "save/renaissance-coast.sav"], "server")
    try:
        time.sleep(2)
        if server.poll() is not None:
            raise RuntimeError("Dedicated server did not stay running")
        server.stdin.write("unpause\n"); server.stdin.flush()
        for name, runtime, duration in (("fork", fork_dir, args.seconds), ("upstream", baseline_dir, 5)):
            # The null driver's tight loop bypasses normal frame pacing and is
            # unsuitable for network sync tests. Use the real Windows driver.
            client, co, ce = start(runtime, ["-v", "win32", "-s", "null", "-m", "null", "-n", "127.0.0.1:39791#255"], name)
            time.sleep(duration)
            server.stdin.write("clients\n"); server.stdin.flush()
            if client.poll() is None:
                client.terminate()
            client.wait(timeout=10)
            co.close(); ce.close()
            time.sleep(1)
        server.stdin.write("quit\n"); server.stdin.flush()
        server.wait(timeout=15)
    finally:
        if server.poll() is None:
            server.terminate(); server.wait(timeout=10)
        out.close(); err.close()
    server_log = (server_dir / "server-stdout.log").read_text()
    client_log = (fork_dir / "fork-stderr.log").read_text()
    if "name: 'Renaissance fork-client'" not in server_log:
        raise RuntimeError("Matching client was not active at the end of the test")
    if "wrong revision" not in server_log or "desync" in client_log.lower():
        raise RuntimeError("Expected upstream rejection or absence of desync not established")
    print(json.dumps({"server_exit": server.returncode, "duration_seconds": args.seconds,
                      "logs": str(output), "note": "Inspect logs for active client, sync errors and upstream rejection."}, indent=2))
