# Licensing and distribution records

Transport Renaissance is an independent, AI-assisted fork. OpenTTD and its contributors retain their attribution. The project name is provisional; no OpenTTD endorsement is claimed. No proprietary Transport Tycoon artwork, sound or music is included.

The engine is GPL version 2; see the preserved root `COPYING.md`, `CREDITS.md`, `README.md`, and source notices. New project code, demo scripts and procedural artwork are distributed under GPL-2.0-only. Generated meadow material is identified in the [asset provenance](art.md); no exclusive rights are asserted over machine-generated material. The combined derived terrain package includes GPL OpenGFX material and is distributed under GPL-2.0-only.

## Runtime contents

| Component | Pinned version | License / attribution record |
|---|---|---|
| OpenTTD | 15.3, `14ec60f248547d4d062a1160f0fc26d742319888`, plus fork commits | GPL-2.0; upstream credits and exceptions retained |
| OpenGFX | 8.0, `e68bd9b7cb60305aa98c687b6836e0e0b08e2847` | GPL-2.0; OpenGFX team, complete author overview retained with art source |
| OpenSFX | 1.0.3 | Sounds: CC-BY-SA-3.0. Other files: GPL-2.0-or-later / CDDL-1.1 dual licensing. Per-sound authors and sources are in its distributed documentation/source archive. No sound modifications. |
| OpenMSX | 0.4.2 | GPL-2.0; original composer credits and MIDI sources retained. No modifications. |
| zlib | 1.3.2 | Zlib license, source `LICENSE`; linked statically |
| libpng | 1.6.59 | Libpng license, source `LICENSE` and `LICENSES`; linked statically |
| liblzma / XZ | 5.8.4 | liblzma: 0BSD; `COPYING` describes other source-file licenses. Only the library is linked. |
| LLVM MinGW C++ runtime / libunwind | 20261020 bundle, Clang 23.1.4 | Apache-2.0 with LLVM exceptions; complete bundle `LICENSE.TXT` retained. The compiler itself is downloaded by bootstrap, not shipped as a game dependency. |

The executable imports `libunwind.dll` plus Windows system libraries. Unused `libc++.dll` and `libwinpthread-1.dll` are not included in the release package. Windows libraries and system fonts are not redistributed.

## Bundled engine libraries

The upstream README is authoritative for these exceptions, and the actual files remain in corresponding source:

- Squirrel and MD5: Zlib license (`src/3rdparty/squirrel/COPYRIGHT` and MD5 source headers).
- fmt and nlohmann JSON: MIT (`LICENSE.rst`, `LICENSE.MIT`).
- OpenGL API headers: MIT (`src/3rdparty/opengl/khrplatform.h`).
- Catch2: Boost Software License 1.0 (test/build dependency).
- ICU script-run helper: Unicode license.
- Monocypher: BSD-2-Clause / CC0, as recorded in its license file.
- OpenTTD Social Integration API: MIT.
- LLVM CMake atomic check: Apache-2.0.

## Source and release procedure

`tools/renaissance/package.py` requires a clean committed source tree and a matching generated executable revision. It creates a portable Windows archive containing the game, base-content packages, custom GRF, demo, instructions, notices, dependency lock, build manifest, and a `sources/` directory. That directory contains the exact fork source (including asset source and build scripts), pinned zlib/libpng/XZ/OpenGFX sources, and the official OpenSFX/OpenMSX source archives. The source archive includes `.ottdrev` so rebuilding an extracted source tree retains the version identity.

Official source archives are hash-verified, not replaced by an unverifiable download promise. The portable binary is not distributed separately from this corresponding-source bundle in this checkpoint. Keep the complete archive when redistributing it. Do not remove source, credits or license files to reduce download size. The GPL notice and corresponding source accompany all GPL components; Creative Commons attribution remains with the unmodified sound package.

Tool and source versions/hashes are in `tools/renaissance/dependencies.json`. Python requirements are pinned in `requirements.txt`. The build tools are not part of the game runtime; their upstream packages retain their licenses. Publishing a release or changing asset provenance requires a fresh manifest review.
