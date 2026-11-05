"""Each test runs in a fresh interpreter: once the GIL is on, it stays on for the process."""

import json
import os
import subprocess
import sys
import textwrap

import pytest

if not __import__('sysconfig').get_config_var('Py_GIL_DISABLED'):
    pytest.skip('requires a free-threaded build', allow_module_level=True)


def run(code: str, **env):
    full_env = {k: v for k, v in os.environ.items() if k not in ('GILGUARD_ACTION', 'PYTHON_GIL')}
    full_env.update(env)
    return subprocess.run(
        [sys.executable, '-c', textwrap.dedent(code)],
        capture_output=True,
        text=True,
        env=full_env,
    )


def report_of(code: str, **env) -> dict:
    body = textwrap.indent(textwrap.dedent(code).strip(), '    ')
    p = run(
        'import json, gilguard\n'
        'try:\n'
        f'{body}\n'
        'except gilguard.GILEnabledError as e:\n'
        '    print(json.dumps(e.report.as_dict()))\n',
        **env,
    )
    assert p.stdout.strip(), p.stderr
    return json.loads(p.stdout.strip().splitlines()[-1])


def test_safe_extension_keeps_gil_off():
    p = run('import gilguard, ftsafe; assert ftsafe.add(2, 3) == 5; print(gilguard.gil_enabled())')
    assert p.returncode == 0, p.stderr
    assert p.stdout.strip() == 'False'
    assert 'global interpreter lock' not in p.stderr  # nothing noisy printed


def test_offender_is_named_with_chain_and_distribution():
    r = report_of('import gilneeder')
    assert r['module'] == 'gilneeder._speedups'
    assert r['chain'] == ['gilneeder', 'gilneeder._speedups']
    assert r['distribution'] == 'gilneeder' and r['version'] == '1.2.0'
    assert r['origin'].endswith('.so') or r['origin'].endswith('.pyd')
    assert r['your_code'] == '<string>:3'
    assert r['imported_by'].endswith(os.path.join('gilneeder', '__init__.py') + ':1')


def test_direct_submodule_import():
    r = report_of('from gilneeder import _speedups')
    assert r['module'] == 'gilneeder._speedups'


def test_importlib_import_module():
    r = report_of("import importlib; importlib.import_module('gilneeder')")
    assert r['module'] == 'gilneeder._speedups'
    assert r['your_code'].startswith('<string>:')


@pytest.mark.parametrize('handler', ['ImportError', 'Exception'])
def test_cannot_be_swallowed_by_optional_import_pattern(handler):
    p = run(f"""
        import gilguard
        try:
            import gilneeder
        except {handler}:
            print("swallowed")
        """)
    assert 'swallowed' not in p.stdout
    assert p.returncode != 0
    assert "GILEnabledError: Importing 'gilneeder._speedups' re-enabled the GIL" in p.stderr


def test_import_that_bypasses_meta_path_is_caught_by_backstop():
    r = report_of("""
        import importlib.util, os, site, glob
        so = glob.glob(os.path.join(site.getsitepackages()[0], 'gilneeder', '_speedups*'))[0]
        spec = importlib.util.spec_from_file_location('gilneeder._speedups', so)
        importlib.util.module_from_spec(spec)
        """)
    assert r['module'] == 'gilneeder._speedups'


def test_gil_already_on_before_gilguard_lists_suspects():
    p = run(
        'import gilneeder, gilguard',
    )
    assert p.returncode != 0
    assert 'already enabled before gilguard was imported' in p.stderr
    assert 'gilneeder._speedups' in p.stderr


def test_python_gil_1_is_reported():
    p = run('import gilguard', PYTHON_GIL='1')
    assert 'PYTHON_GIL=1' in p.stderr


def test_python_gil_0_means_nothing_fires():
    p = run('import gilguard, gilneeder; print(gilguard.gil_enabled())', PYTHON_GIL='0')
    assert p.returncode == 0 and p.stdout.strip() == 'False'


def test_warn_mode_reports_and_continues():
    p = run("import gilguard, gilneeder; print('ran', gilneeder.add(1, 1))", GILGUARD_ACTION='warn')
    assert p.returncode == 0
    assert 'ran 2' in p.stdout
    assert 'GILGuardWarning' in p.stderr and 'gilneeder._speedups' in p.stderr
    assert p.stderr.count('re-enabled the GIL') == 1  # once, not duplicated by CPython's own warning


def test_off_mode():
    p = run('import gilguard, gilneeder', GILGUARD_ACTION='off')
    assert p.returncode == 0


def test_threaded_imports():
    p = run("""
        import gilguard, threading, json
        errs = []
        def go():
            try:
                import gilneeder
            except gilguard.GILEnabledError as e:
                errs.append(e.report.module)
        ts = [threading.Thread(target=go) for _ in range(8)]
        [t.start() for t in ts]; [t.join() for t in ts]
        print(json.dumps(errs))
        """)
    errs = json.loads(p.stdout)
    assert 'gilneeder._speedups' in errs


def test_scan_cli():
    p = subprocess.run(
        [sys.executable, '-m', 'gilguard', '--json', 'gilneeder', 'ftsafe', 'json'], capture_output=True, text=True
    )
    assert p.returncode == 1, p.stderr
    res = json.loads(p.stdout)
    assert res['gilneeder']['status'] == 'gil'
    assert res['gilneeder']['report']['module'] == 'gilneeder._speedups'
    assert res['ftsafe']['status'] == 'ok'
    assert res['json']['status'] == 'ok'
