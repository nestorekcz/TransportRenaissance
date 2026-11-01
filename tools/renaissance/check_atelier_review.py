"""Check the committed art review without Blender, NML or a running game.

Use --workspace to additionally verify the delivered binary/source artifacts.
This checks source-to-evidence consistency; it does not rerun native visual QA.
GPL-2.0-only.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from temperate_plan import ROOT, infrastructure, world, details


REVIEW = ROOT / 'docs/renaissance/atelier'
EVIDENCE = REVIEW / 'evidence'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path)
    args = parser.parse_args()

    scripts = [p for p in Path(__file__).parent.glob('*.py')
               if p.name.startswith(('atelier_', 'future_heritage_', 'temperate_'))]
    for path in scripts:
        compile(path.read_text(encoding='utf-8'), str(path), 'exec')

    jobs = infrastructure() + world(EVIDENCE / 'approved-coverage.json') + details()
    keys = {j['key'] for j in jobs}
    assert len(keys) == len(jobs), 'Duplicate source assignments'
    coverage = read(EVIDENCE / 'coverage.json')
    slots = {r['key'] for r in coverage}
    assert len(slots) == len(coverage), 'Duplicate exported assignments'
    assert keys <= slots, 'A source view is absent from the export'
    preserved = {r['sprite_id'] for r in read(EVIDENCE / 'approved-coverage.json')
                 if r['category'] in ('building', 'building-ground', 'tree')}
    assert not preserved.intersection(r.get('sprite_id') for r in coverage), 'Approved art overwritten'

    audit = read(EVIDENCE / 'audit-summary.json')
    build = read(EVIDENCE / 'build.json')
    validation = read(EVIDENCE / 'validation.json')
    assert not build['partial']
    assert len(jobs) == validation['new_model_view_collections'] == audit['model_view_jobs']
    assert len(coverage) == build['sprites'] == validation['new_logical_sprite_slots']
    assert Counter(r['category'] for r in coverage) == audit['new_categories']
    assert sum(audit['source_slot_status_counts'].values()) == audit['reviewed_source_raster_slots']
    assert build['sha256'] == validation['runtime_grf_sha256']

    bounds = read(EVIDENCE / 'verification/render-bounds.json')
    assert {r['key'] for r in bounds} == keys
    for row in bounds:
        left, top, right, bottom = row['alpha_bounds']
        width, height = row['dimensions']
        assert 0 < left < right < width and 0 < top < bottom < height, row['key']
    fleet = read(EVIDENCE / 'fleet-engine-audit.json')
    assert fleet['engines'] == 256 and fleet['resolved_directions'] == 2048
    assert not fleet['non_graphics_property_differences']
    assert not validation['native_fleet']['differences_from_approved_fleet']
    compatibility = read(EVIDENCE / 'verification/compatibility.json')
    assert compatibility['stock_save_written'] and compatibility['fork_reload']['exit_code'] == 0
    performance = read(EVIDENCE / 'verification/performance.json')
    for row in performance:
        assert row['exit_code'] == 0
        assert len(row['distinct_tiles_per_powered_vehicle']) == 9
        assert min(row['distinct_tiles_per_powered_vehicle'].values()) > 1
    context = read(EVIDENCE / 'verification/performance-context.json')
    assert context['delivered_world_pack_sha256'] == build['sha256']

    captures = sorted((REVIEW / 'review').glob('*.png'))
    for path in captures:
        with path.open('rb') as stream:
            header = stream.read(24)
        assert header[:8] == b'\x89PNG\r\n\x1a\n', path
        assert struct.unpack('>II', header[16:24]) == (1600, 1000), path

    manifest = read(EVIDENCE / 'delivery-manifest.json')
    if args.workspace:
        for row in manifest['artifacts']:
            path = args.workspace / row['path']
            assert path.stat().st_size == row['bytes'], path
            assert digest(path) == row['sha256'], path
    print(f'PASS: {len(scripts)} source scripts; {len(jobs)} model views; '
          f'{len(coverage)} sprite assignments; {len(captures)} native review images.')
    print('Recorded native evidence is consistent. No engine benchmark was rerun by this check.')


if __name__ == '__main__':
    main()
