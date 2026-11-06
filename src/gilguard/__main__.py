"""python -m gilguard [module ...]

Imports each module in a fresh interpreter with gilguard active and reports
which ones re-enable the GIL. With no arguments, scans every top-level module
of every installed distribution.

A fresh process per module is required: once the GIL is on it stays on, so a
single process can only ever detect the first offender.

Exits 1 when any module re-enables the GIL (with --strict, also when any fails
to import or times out), 2 when this is not a free-threaded build, and 0
otherwise. --json prints the results as data instead of the table.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

_CHILD = r"""
import json, sys
import gilguard
try:
    __import__(sys.argv[1])
except gilguard.GILEnabledError as e:
    print(json.dumps({"status": "gil", "report": e.report.as_dict()}))
    sys.exit(0)
except BaseException as e:
    print(json.dumps({"status": "error", "error": f"{type(e).__name__}: {e}"}))
    sys.exit(0)
print(json.dumps({"status": "ok"}))
"""

_SKIP = {'gilguard', 'pip', 'setuptools', '_distutils_hack', 'pkg_resources', 'wheel'}


def _installed_modules() -> list[str]:
    from importlib import metadata

    names = {n for n in metadata.packages_distributions() if n.isidentifier()}
    return sorted(n for n in names - _SKIP if not n.startswith('_'))


def _check(module: str, timeout: float) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ('GILGUARD_ACTION', 'PYTHON_GIL')}
    try:
        proc = subprocess.run(
            [sys.executable, '-c', _CHILD, module],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': f'timed out after {timeout:.0f}s'}
    last = proc.stdout.strip().splitlines()[-1:] or ['']
    try:
        return json.loads(last[0])
    except json.JSONDecodeError:
        err = (proc.stderr.strip().splitlines() or ['no output'])[-1]
        return {'status': 'error', 'error': err}


def main(argv: list[str] | None = None) -> int:
    import gilguard

    parser = argparse.ArgumentParser(prog='python -m gilguard', description=__doc__.split('\n\n')[1])
    parser.add_argument('modules', nargs='*', help='modules to check (default: all installed)')
    parser.add_argument('--json', action='store_true', help='print results as JSON')
    parser.add_argument('--timeout', type=float, default=60.0, help='seconds per module (default 60)')
    parser.add_argument('-j', '--jobs', type=int, default=os.cpu_count() or 4)
    parser.add_argument(
        '--strict',
        action='store_true',
        help='also exit 1 when a module fails to import or times out, not only when it re-enables the GIL',
    )
    args = parser.parse_args(argv)

    if not gilguard.is_free_threaded_build():
        print(
            'gilguard: this is not a free-threaded Python build; run the scan with python3.13t / python3.14t.',
            file=sys.stderr,
        )
        return 2

    modules = args.modules or _installed_modules()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = dict(zip(modules, pool.map(lambda m: _check(m, args.timeout), modules)))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        offenders = {m: r for m, r in results.items() if r['status'] == 'gil'}
        errors = {m: r for m, r in results.items() if r['status'] == 'error'}
        ok = len(results) - len(offenders) - len(errors)
        for mod, r in offenders.items():
            rep = r['report']
            dist = f'{rep["distribution"]} {rep["version"]}' if rep['distribution'] else '?'
            print(f'GIL    {mod:<24} via {rep["module"]}  [{dist}]')
        for mod, r in errors.items():
            print(f'ERROR  {mod:<24} {r["error"]}')
        print(f'\n{len(results)} checked: {ok} ok, {len(offenders)} re-enable the GIL, {len(errors)} failed to import.')
        if errors and not args.strict:
            print('Modules that failed to import were not checked. Pass --strict to fail the run on them.')
        print(
            'Note: only import-time loads are checked. '
            'Extensions a package loads lazily on first use will not show up here.'
        )

    failing = ('gil', 'error') if args.strict else ('gil',)
    return 1 if any(r['status'] in failing for r in results.values()) else 0


if __name__ == '__main__':
    sys.exit(main())
