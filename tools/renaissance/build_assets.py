#!/usr/bin/env python3
"""Compile the Renaissance Meadow static NewGRF. GPL-2.0-only.

Editable source material + OpenGFX's GPL silhouettes -> deterministic sprite
atlases, 8-bit fallback, 32-bit normal/2x/4x alternatives, and an NML package.
Generated files belong in the requested output directory, never in source.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import sys

from PIL import Image
from nml.palette import raw_palette_data

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "media/renaissance/source"
# Source geometry from OpenGFX 8.0 tmpl_groundtiles, GPL-2.0-only.
X = [0, 80, 160, 240, 320, 398, 478, 558, 638, 718, 798, 878, 958, 1038, 1118, 1196, 1276, 1356, 1436]
HEIGHT = [31, 31, 23, 23, 31, 31, 23, 23, 39, 39, 31, 31, 39, 39, 31, 47, 15, 31, 31]
YOFF = [0] * 8 + [-8] * 7 + [-16, 0, -8, -8]
PALETTE = raw_palette_data[0]


def input_hash():
    digest = hashlib.sha256()
    for path in [Path(__file__), *sorted(SOURCE.rglob("*"))]:
        if path.is_file():
            digest.update(str(path.relative_to(ROOT)).replace("\\", "/").encode())
            digest.update(path.read_bytes())
    for package in ("Pillow", "nml", "ply"):
        digest.update(f"{package}={importlib.metadata.version(package)}".encode())
    return digest.hexdigest()


def palette_image(size):
    im = Image.new("P", size, 0)
    im.putpalette(PALETTE)
    return im


def fallback(image):
    """Quantize against only static, non-company colours; reserve index 0."""
    pal = Image.new("P", (16, 16))
    # Exclude animated entries and company-colour ramp 198..205.
    safe = [i for i in range(1, 215) if not 198 <= i <= 205]
    colours = [PALETTE[i * 3:i * 3 + 3] for i in safe]
    padded = colours + [colours[-1]] * (256 - len(colours))
    pal.putpalette([v for c in padded for v in c])
    quantized = image.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE)
    out = palette_image(image.size)
    out.putdata([safe[min(index, len(safe) - 1)] if a >= 128 else 0
                 for index, a in zip(quantized.getdata(), image.getchannel("A").getdata())])
    return out


def compile_assets(out):
    out.mkdir(parents=True, exist_ok=True)
    (out / "lang").mkdir(exist_ok=True)
    (out / "lang/english.lng").write_text(
        "##grflangid 0x01\nSTR_NAME :Renaissance Meadow\n"
        "STR_DESC :Independent Transport Renaissance terrain slice. Temperate grass and regrowth, 32-bit 1x/2x/4x sprites, 8-bit fallback; soft steam frames. GPL v2.\n", encoding="utf-8")
    material = Image.open(SOURCE / "meadow-source.png").convert("RGB").resize((256, 256), Image.Resampling.LANCZOS)
    shape = Image.open(SOURCE / "opengfx-ground-mask.png")
    rgb_shape = shape.convert("RGB")
    # Opposite edges sample identical source positions, avoiding a hard tile seam.
    tex = material.load()
    blocks = []
    inventory = []
    for scale in (1, 2, 4):
        atlas = Image.new("RGBA", (19 * 66 * scale, 4 * 49 * scale))
        for stage in range(4):
            for slope in range(19):
                tile = Image.new("RGBA", (64 * scale, HEIGHT[slope] * scale))
                pixels = tile.load()
                # Preserve verified pixel silhouettes and anchors at every zoom.
                for py in range(tile.height):
                    for px in range(tile.width):
                        sx, sy = px // scale, py // scale
                        original = shape.getpixel((X[slope] + 1 + sx, 1 + sy))
                        if original == 0:
                            continue
                        # Project material in tile space. Mirrored periodic sampling is seam-safe.
                        wx = ((px / scale - 31) / 32 + (py / scale + YOFF[slope]) / 16) / 2
                        wy = ((py / scale + YOFF[slope]) / 16 - (px / scale - 31) / 32) / 2
                        u = int(abs((wx % 2) - 1) * 255)
                        v = int(abs((wy % 2) - 1) * 255)
                        r, g, b = tex[u, v]
                        # Calm low-contrast colour range; avoid a noisy high-zoom checkerboard.
                        luminance = (r * 0.25 + g * 0.6 + b * 0.15) / 128
                        old = rgb_shape.getpixel((X[slope] + 1 + sx, 1 + sy))
                        shade = 0.88 + min(0.22, sum(old) / (3 * 255) * 0.4)
                        grass = (r * 0.63, g * 0.73, b * 0.8 + 5)
                        soil = (100 + luminance * 14, 81 + luminance * 11, 56 + luminance * 9)
                        growth = stage / 3
                        # Tiny reproducible regrowth variation at 2x and 4x, not random per build.
                        noise = math.sin(wx * 41 + math.sin(wy * 29)) * math.sin(wy * 53)
                        blend = max(0, min(1, growth + (noise * 0.2 if stage in (1, 2) else 0)))
                        colour = tuple(round((a * blend + c * (1 - blend)) * shade) for a, c in zip(grass, soil))
                        pixels[px, py] = (*colour, 255)
                atlas.paste(tile, (slope * 66 * scale, stage * 49 * scale))
        atlas.save(out / f"meadow-{scale}x.png")
        if scale == 1:
            fallback(atlas).save(out / "meadow-8bpp.png")
    for stage in range(4):
        name = f"meadow_stage_{stage}"
        blocks.append(f'replace {name}({3924 + stage * 19}, "meadow-8bpp.png") {{')
        for slope in range(19):
            blocks.append(f"  [{slope * 66}, {stage * 49}, 64, {HEIGHT[slope]}, -31, {YOFF[slope]}, NOCROP]")
            inventory.append({"sprite": 3924 + stage * 19 + slope, "category": "temperate regrowth", "stage": stage, "slope": slope})
        blocks.append("}")
        for scale, zoom in ((1, "NORMAL"), (2, "IN_2X"), (4, "IN_4X")):
            blocks.append(f'alternative_sprites({name}, ZOOM_LEVEL_{zoom}, BIT_DEPTH_32BPP, "meadow-{scale}x.png") {{')
            for slope in range(19):
                blocks.append(f"  [{slope * 66 * scale}, {stage * 49 * scale}, {64 * scale}, {HEIGHT[slope] * scale}, {-31 * scale}, {YOFF[slope] * scale}, NOCROP]")
            blocks.append("}")
    # Retexture the ground around inherited rough/rock formations and infrastructure.
    # Their silhouettes, stones, rails, sleepers and road markings remain attributed OpenGFX art.
    surfaces = json.loads((SOURCE / "ground-surfaces.json").read_text())
    for category, first, file, count in (("rough ground", 4000, "opengfx-rough.png", 23), ("rocky ground", 4023, "opengfx-rocks.png", 19)):
        for index in range(count):
            slope = index if index < 19 else 0
            x = X[index] if index < 19 else 1510 + (index - 19) * 80
            surfaces.append({"sprite": first + index, "category": category, "source": file,
                             "rect": [x + 1, 1, 64, HEIGHT[slope], -31, YOFF[slope]]})
    source_images = {row["source"]: Image.open(SOURCE / row["source"]) for row in surfaces}
    for scale in (1, 2, 4):
        surface_atlas = Image.new("RGBA", (len(surfaces) * 66 * scale, 49 * scale))
        for index, row in enumerate(surfaces):
            x, y, width, height, dx, dy = row["rect"]
            original = source_images[row["source"]]
            colours = original.convert("RGB")
            for py in range(height * scale):
                for px in range(width * scale):
                    sx, sy = x + px // scale, y + py // scale
                    if original.getpixel((sx, sy)) == 0:
                        continue
                    old_r, old_g, old_b = colours.getpixel((sx, sy))
                    if old_g > old_r * 1.15 and old_b < old_g * 0.75:
                        wx = ((px / scale - 31) / 32 + (py / scale + dy) / 16) / 2
                        wy = ((py / scale + dy) / 16 - (px / scale - 31) / 32) / 2
                        r, g, b = tex[int(abs((wx % 2) - 1) * 255), int(abs((wy % 2) - 1) * 255)]
                        shade = 0.88 + min(0.22, (old_r + old_g + old_b) / (3 * 255) * 0.4)
                        # Preserve rough ground's sparse tufts as local variations.
                        if row["category"] == "rough ground":
                            shade *= 0.84 + min(0.28, old_g / 350)
                        colour = (round(r * 0.63 * shade), round(g * 0.73 * shade), round((b * 0.8 + 5) * shade), 255)
                    else:
                        colour = (old_r, old_g, old_b, 255)
                    surface_atlas.putpixel((index * 66 * scale + px, py), colour)
        surface_atlas.save(out / f"surfaces-{scale}x.png")
        if scale == 1:
            fallback(surface_atlas).save(out / "surfaces-8bpp.png")
    for index, row in enumerate(surfaces):
        x, y, width, height, dx, dy = row["rect"]
        name = f"surface_{row['sprite']}"
        blocks.extend([f'replace {name}({row["sprite"]}, "surfaces-8bpp.png") {{',
                       f"  [{index * 66}, 0, {width}, {height}, {dx}, {dy}, NOCROP]", "}"])
        for scale, zoom in ((1, "NORMAL"), (2, "IN_2X"), (4, "IN_4X")):
            blocks.extend([f'alternative_sprites({name}, ZOOM_LEVEL_{zoom}, BIT_DEPTH_32BPP, "surfaces-{scale}x.png") {{',
                           f"  [{index * 66 * scale}, 0, {width * scale}, {height * scale}, {dx * scale}, {dy * scale}, NOCROP]", "}"])
        inventory.append({"sprite": row["sprite"], "category": row["category"], "inherited_structure": True})
    terrain_count = len(blocks)
    # Original code-authored alpha steam sprites; retain the five engine frames and timing.
    sizes = (8, 10, 12, 14, 16)
    for scale in (1, 2, 4):
        steam = Image.new("RGBA", (90 * scale, 18 * scale))
        for frame, size in enumerate(sizes):
            for py in range(size * scale):
                for px in range(size * scale):
                    u = (px + 0.5) / (size * scale) * 2 - 1
                    v = (py + 0.5) / (size * scale) * 2 - 1
                    density = 0.0
                    for cx, cy, radius in ((-0.25, 0.1, 0.64), (0.22, -0.15, 0.63), (0.05, 0.25, 0.57)):
                        d = ((u - cx) ** 2 + (v - cy) ** 2) / radius ** 2
                        density = max(density, max(0.0, 1 - d) ** 0.6)
                    alpha = round(density * (205 - frame * 28))
                    light = round(226 + (1 - v) * 8)
                    steam.putpixel((frame * 18 * scale + px, py), (light, light, max(0, light - 7), alpha))
        steam.save(out / f"steam-{scale}x.png")
        if scale == 1:
            fallback(steam).save(out / "steam-8bpp.png")
    blocks.append('replace soft_steam(3079, "steam-8bpp.png") {')
    for frame, size in enumerate(sizes):
        blocks.append(f"  [{frame * 18}, 0, {size}, {size}, {-size // 2}, {-size // 2}, NOCROP]")
        inventory.append({"sprite": 3079 + frame, "category": "steam", "frame": frame})
    blocks.append("}")
    for scale, zoom in ((1, "NORMAL"), (2, "IN_2X"), (4, "IN_4X")):
        blocks.append(f'alternative_sprites(soft_steam, ZOOM_LEVEL_{zoom}, BIT_DEPTH_32BPP, "steam-{scale}x.png") {{')
        for frame, size in enumerate(sizes):
            blocks.append(f"  [{frame * 18 * scale}, 0, {size * scale}, {size * scale}, {-size // 2 * scale}, {-size // 2 * scale}, NOCROP]")
        blocks.append("}")
    header = 'grf { grfid: "TR\\01\\01"; name: string(STR_NAME); desc: string(STR_DESC); version: 1; min_compatible_version: 1; }\n'
    # Do not replace other climates' terrain. Steam remains universally cosmetic.
    nml = header + "if (climate == CLIMATE_TEMPERATE) {\n" + "\n".join(blocks[:terrain_count]) + "\n}\n" + "\n".join(blocks[terrain_count:]) + "\n"
    (out / "renaissance-meadow.nml").write_text(nml, encoding="utf-8")
    subprocess.run([sys.executable, "-m", "nml.main", "--grf", "renaissance-meadow.grf", "renaissance-meadow.nml"], cwd=out, check=True)
    package = out / "renaissance-meadow.grf"
    manifest = {"version": 1, "input_sha256": input_hash(), "coverage": inventory, "sprite_count": len(inventory), "sha256": hashlib.sha256(package.read_bytes()).hexdigest(), "bytes": package.stat().st_size, "zoom_scales": [1, 2, 4], "static_grf": True}
    (out / "asset-build.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "coverage"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="Exit successfully only if the compiled GRF matches these inputs")
    args = parser.parse_args()
    if args.check:
        try:
            metadata = json.loads((args.output / "asset-build.json").read_text())
            package = args.output / "renaissance-meadow.grf"
            valid = metadata["input_sha256"] == input_hash() and metadata["sha256"] == hashlib.sha256(package.read_bytes()).hexdigest()
        except (OSError, KeyError, ValueError):
            valid = False
        sys.exit(0 if valid else 1)
    compile_assets(args.output.resolve())
