"""Emit the optional offline fixture patch without modifying engine sources.

The reviewed C++ helper bodies are in atelier_console_helpers.inc. This generator
targets the exact art checkpoint; apply its output only to a separate checkout.
GPL-2.0-only.
"""
import argparse
import difflib
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
BASE = 'f1fa0af2766d07820b15166179585b0ae4bbcd95'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base = subprocess.check_output(
        ['git', '-C', str(ROOT), 'show', BASE + ':src/console_cmds.cpp'],
        text=True, encoding='utf-8')
    modified = base

    def insert_after(anchor, addition):
        nonlocal modified
        assert modified.count(anchor) == 1, anchor
        modified = modified.replace(anchor, anchor + addition)

    insert_after('#include "engine_base.h"\n', ''.join(
        f'#include "{name}"\n' for name in
        ('newgrf_engine.h', 'vehicle_base.h', 'vehicle_gui.h', 'spritecache.h')))
    insert_after('#include "misc_cmd.h"\n', ''.join(
        f'#include "{name}"\n' for name in
        ('town_cmd.h', 'tree_cmd.h', 'tree_map.h', 'core/backup_type.hpp')))
    bodies = Path(__file__).with_name('atelier_console_helpers.inc').read_text(encoding='utf-8')
    anchor = 'static bool ConZoomToLevel(std::span<std::string_view> argv)'
    assert modified.count(anchor) == 1
    modified = modified.replace(anchor, bodies.rstrip() + '\n\n' + anchor)
    insert_after('\tIConsole::CmdRegister("zoomto",                  ConZoomToLevel);\n',
                 '\tIConsole::CmdRegister("atelier_view",            ConAtelierView, ConHookNewGRFDeveloperTool);\n')
    insert_after('\tIConsole::CmdRegister("reload_newgrfs",          ConNewGRFReload,     ConHookNewGRFDeveloperTool);\n',
                 '\tIConsole::CmdRegister("atelier_house",          ConAtelierHouse,     ConHookNewGRFDeveloperTool);\n'
                 '\tIConsole::CmdRegister("atelier_tree",           ConAtelierTree,      ConHookNewGRFDeveloperTool);\n'
                 '\tIConsole::CmdRegister("atelier_fleet_audit",    ConAtelierFleetAudit, ConHookNewGRFDeveloperTool);\n'
                 '\tIConsole::CmdRegister("atelier_fleet_shop",     ConAtelierFleetShop, ConHookNewGRFDeveloperTool);\n')
    patch = ''.join(difflib.unified_diff(base.splitlines(True), modified.splitlines(True),
                                       fromfile='a/src/console_cmds.cpp', tofile='b/src/console_cmds.cpp'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(patch)
    print(f'Wrote optional fixture patch: {args.output}')


if __name__ == '__main__':
    main()
