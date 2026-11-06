---
name: gilguard
description: >
  Catch the import that re-enables the GIL on free-threaded Python (3.13t, 3.14t, 3.15t). Use when adding gilguard to an app, test suite or CI, when a GILEnabledError or GILGuardWarning shows up, when choosing between raise, warn and off, or when auditing an environment with python -m gilguard.
license: MIT
compatibility: Requires Python >=3.13. Does its real work on a free-threaded build; on a standard build it raises at import unless GILGUARD_ACTION=off.
---

# gilguard

On a free-threaded build, importing an extension module that doesn't declare `Py_mod_gil` turns the GIL back on for the rest of the process, with one easy-to-miss `RuntimeWarning`. It cannot be turned off again. gilguard turns that moment into `GILEnabledError`, naming the module, the distribution, the import chain and the line of the user's code that started it.

## Install

```bash
uv pip install gilguard   # or: pip install gilguard
```

## Use

Make it the first import of the process (`main.py`, the ASGI app module, `manage.py`, `__main__.py`):

```python
import gilguard  # must be first

import pandas  # raises GILEnabledError here if anything in its import tree needs the GIL
```

Tests: `pytest -p gilguard`, or `addopts = "-p gilguard"` under `[tool.pytest.ini_options]`. Prefer `-p` over an import in `conftest.py`; it loads before any test code.

CI: `python -m gilguard --strict` imports every installed package in its own interpreter and exits 1 on any offender (with `--strict`, also when a package fails to import). Run it only on free-threaded jobs; it exits 2 on a standard build.

## Rules

- `import gilguard` must come before every other import. It can only watch imports that happen after it. If the GIL is already on when it loads, it raises at once and lists the loaded third-party extension modules as suspects.
- `GILEnabledError` derives from `BaseException`. `except Exception:` and `except ImportError:` do not catch it, on purpose. Never write a handler that catches it and carries on; the GIL stays on regardless. Log and re-raise.
- Only the first flip in a process is reported. Later imports can't turn the GIL on again. To find every offender, use `python -m gilguard`.
- A clean run means the imports that ran kept the GIL off. It is not proof of thread safety, and not proof of a speedup from threads.
- The scanner only sees import-time loads. Extensions loaded lazily on first use are caught by running the test suite under `pytest -p gilguard`.
- On a standard (GIL) build gilguard raises at import. Set `GILGUARD_ACTION=off` for those jobs rather than wrapping the import in try/except.
- `PYTHON_GIL=0` keeps the GIL off regardless, so gilguard never fires under it. `PYTHON_GIL=1` is reported as the cause.
- The error is raised in the thread that ran the import. In a worker thread, only that thread dies and the process can exit 0. Install a `threading.excepthook` that calls `os._exit(1)` on `GILEnabledError` if a flip anywhere must stop the program.
- `install(action='warn')` after import switches mode without adding a second hook. `install(action='off')` removes the guard, the same as `uninstall()`.

## Decision table

| Need | Use |
|---|---|
| Fail fast in an app | `import gilguard` first; the default action is `raise` |
| First pass over an existing app without taking it down | `GILGUARD_ACTION=warn`, alert on `GILGuardWarning` |
| Same code on standard and free-threaded builds | `GILGUARD_ACTION=off` on the standard-build jobs |
| List every offender in an environment | `python -m gilguard` (or the `gilguard` command); `--json` for data |
| Catch lazily loaded extensions | `pytest -p gilguard` |
| Fail CI on packages that couldn't be checked | `python -m gilguard --strict` |
| Re-check one package after an upgrade | `python -m gilguard somepkg` |
| Get the report as data | `exc.report.as_dict()` |
| Is this a `t` build? Is the GIL on right now? | `gilguard.is_free_threaded_build()`, `gilguard.gil_enabled()` |

## API

- `install(action: str | None = None) -> None`. Called by `import gilguard`. `action` is `"raise"`, `"warn"` or `"off"`; `None` reads `GILGUARD_ACTION`. Raises `ValueError` on anything else, and `GILEnabledError` on a standard build or an already-enabled GIL.
- `uninstall() -> None`. Removes the hook. Later imports go unguarded.
- `GILEnabledError(BaseException)`. `.report` is a `GILReport`; `str(exc)` is the formatted report.
- `GILGuardWarning(RuntimeWarning)`. Emitted in `warn` mode with the same text.
- `GILReport` dataclass. `reason` (`"import"`, `"already-enabled"`, `"gil-build"`), `module`, `origin`, `distribution`, `version`, `chain`, `imported_by`, `your_code`, `gil_flag`, `suspects`; methods `.as_dict()` and `.format()`.
- `is_free_threaded_build() -> bool`, `gil_enabled() -> bool`.

## Reading a report

```text
gilguard.GILEnabledError: Importing 'gilneeder._speedups' re-enabled the GIL.

  Module:       gilneeder._speedups                        <- the extension that flipped it
  File:         .../gilneeder/_speedups.cpython-314t-x86_64-linux-gnu.so
  Distribution: gilneeder 1.2.0                            <- what to upgrade, pin or replace
  Import chain: gilneeder -> gilneeder._speedups
  Your code:    /home/me/app.py:5                          <- where the chain started
  Imported by:  .../gilneeder/__init__.py:1                <- the statement that loaded it
```

Fix order: upgrade the distribution to a release with `cp3XXt` wheels, report the module name upstream, replace it, run with `warn` meanwhile, and use `PYTHON_GIL=0` only for extensions verified thread-safe. For an extension you own, add `{Py_mod_gil, Py_MOD_GIL_NOT_USED}` to its module slots (Cython: `# cython: freethreading_compatible = True`; pybind11: `py::mod_gil_not_used()`; PyO3: `#[pymodule(gil_used = false)]`).

## Resources

- [Full documentation](https://mkennedy.codes/docs/gilguard/)
- [Fixing what it finds](https://mkennedy.codes/docs/gilguard/user-guide/fixing-an-offender.html)
- [Tests and CI](https://mkennedy.codes/docs/gilguard/user-guide/tests-and-ci.html)
- [llms.txt](https://mkennedy.codes/docs/gilguard/llms.txt), an index of the API reference
- [llms-full.txt](https://mkennedy.codes/docs/gilguard/llms-full.txt), the full API reference and user guide
- [Source code](https://github.com/mikeckennedy/gilguard)
