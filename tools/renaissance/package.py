"""Package a committed native checkpoint with notices and corresponding source. GPL-2.0-only."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

REPO = Path(__file__).resolve().parents[2]
WORKSPACE = REPO.parent
ARTIFACTS = WORKSPACE / "artifacts"


def git(*arguments, cwd=REPO):
    return subprocess.check_output(["git", *arguments], cwd=cwd, text=True).strip()


def archive_source(source, target):
    subprocess.run(["git", "archive", "--format=zip", f"--output={target}", "HEAD"], cwd=source, check=True)


def package():
    if git("status", "--porcelain"):
        raise RuntimeError("Commit all source changes before packaging")
    revision = git("rev-parse", "HEAD")
    generated = (ARTIFACTS / "fork-build/generated/rev.cpp").read_text()
    if f'_openttd_revision_hash = "{revision}"' not in generated or '_openttd_revision_modified = 0;' not in generated:
        raise RuntimeError("Rebuild the clean committed revision before packaging")
    version = re.search(r'_openttd_revision = "([^"]+)"', generated)[1]
    lock = json.loads((REPO / "tools/renaissance/dependencies.json").read_text())
    release = ARTIFACTS / "release" / f"TransportRenaissance-{revision[:10]}-windows-x64"
    release.mkdir(parents=True, exist_ok=False)
    runtime = ARTIFACTS / "fork-runtime"
    for name in ("openttd.exe", "libunwind.dll", "openttd.cfg", "coastal-demo.cfg", "Launch-TransportRenaissance.ps1", "Launch-TransportRenaissance.cmd"):
        shutil.copy2(runtime / name, release / name)
    for name in ("baseset", "newgrf", "lang", "game"):
        shutil.copytree(runtime / name, release / name)
    for name in ("save", "scripts", "scenario/heightmap", "sources", "licenses"):
        (release / name).mkdir(parents=True, exist_ok=True)
    demo = REPO / "media/renaissance/demo"
    for save in demo.glob("*.sav"):
        shutil.copy2(save, release / "save")
    for save in (REPO / "media/renaissance/regional").glob("*.sav"):
        shutil.copy2(save, release / "save")
    shutil.copy2(REPO / "media/renaissance/regional/regional-flat.png", release / "scenario/heightmap")
    shutil.copy2(demo / "renaissance-coast.png", release / "scenario/heightmap")
    shutil.copy2(runtime / "scripts/game_start.scr", release / "scripts")
    # Preserve repository-relative guide links in the portable distribution.
    shutil.copytree(REPO / "docs", release / "docs")
    for name in ("COPYING.md", "CREDITS.md", "README.md", "COMPILING.md", "CONTRIBUTING.md"):
        shutil.copy2(REPO / name, release / name)
    (release / "START-HERE.md").write_text(
        "# Transport Renaissance — independent OpenTTD fork\n\n"
        "Double-click Launch-TransportRenaissance.cmd to open the main menu. Regional development is disabled by default.\n\n"
        "To enable it, open Settings > Environment > Towns > Regional development before creating a temperate world.\n\n"
        "Use Load Game > regional-builder.sav for New Haven, or renaissance-coast.sav for the coal railway.\n\n"
        "Load save/renaissance-attention.sav for a deliberately underserved-station example.\n\n"
        "Read [the guide](docs/renaissance/README.md) for controls/build instructions and "
        "[verification](docs/renaissance/verification.md) for tested limits.\n"
        "Corresponding source is included in sources/. Keep it and all notices when redistributing.\n"
        "This is a limited first playable, not a complete graphics overhaul. No official OpenTTD affiliation.\n")
    shutil.copy2(REPO / "tools/renaissance/dependencies.json", release)
    shutil.copy2(ARTIFACTS / "assets/asset-build.json", release)
    source_zip = release / "sources/TransportRenaissance-source.zip"
    archive_source(REPO, source_zip)
    date = git("show", "-s", "--format=%cs", "HEAD").replace("-", "")
    with zipfile.ZipFile(source_zip, "a", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(".ottdrev", f"{version}\t{date}\t0\t{revision}\t0\t0\n")
    for library in lock["libraries"]:
        source = WORKSPACE / "tools/sources" / library["name"]
        if git("rev-parse", "HEAD", cwd=source) != library["commit"] or git("status", "--porcelain", cwd=source):
            raise RuntimeError(f"Dependency source differs from lock: {source}")
        archive_source(source, release / "sources" / f'{library["name"]}-{library["tag"]}-source.zip')
        notice = release / "licenses" / library["name"]
        notice.mkdir()
        for file in source.iterdir():
            if file.is_file() and (file.name.upper().startswith(("LICENSE", "COPYING", "README"))):
                shutil.copy2(file, notice)
    for component in lock["content"]:
        if "source_url" in component:
            source = ARTIFACTS / "source-archives" / component["source_url"].split("/")[-1]
            if hashlib.sha256(source.read_bytes()).hexdigest() != component["source_sha256"]:
                raise RuntimeError(f"Source checksum mismatch: {source}")
            shutil.copy2(source, release / "sources")
    shutil.copy2(WORKSPACE / "tools" / lock["compiler"]["name"] / "LICENSE.TXT", release / "licenses/LLVM-LICENSE.TXT")
    for file in (REPO / "src/3rdparty").rglob("*"):
        if file.is_file() and (file.name.upper().startswith(("LICENSE", "COPYRIGHT")) or file.name == "khrplatform.h"):
            dest = release / "licenses" / file.relative_to(REPO / "src")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, dest)
    manifest = {"name": "Transport Renaissance", "independent_fork": True, "version": version,
                "commit": revision, "upstream": lock["upstream"], "platform": "Windows x64",
                "exe_sha256": hashlib.sha256((release / "openttd.exe").read_bytes()).hexdigest(),
                "build": "Release, assertions on; LLVM MinGW; see dependencies.json and source build scripts",
                "files": {str(p.relative_to(release)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(release.rglob("*")) if p.is_file()}}
    (release / "BUILD-MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    archive = shutil.make_archive(str(release), "zip", release.parent, release.name)
    Path(archive + ".sha256").write_text(hashlib.sha256(Path(archive).read_bytes()).hexdigest() + "  " + Path(archive).name + "\n")
    print(archive)


if __name__ == "__main__":
    package()
