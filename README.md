<p align="center">
  <img src="https://mkennedy-shared.nyc3.digitaloceanspaces.com/github/gilguard-banner.png" alt="gilguard: Catch the import. Name the culprit. Keep threads free." width="850">
</p>

# gilguard

Raise a detailed error the moment an import re-enables the GIL on free-threaded Python.

Full documentation: [mkennedy.codes/docs/gilguard](https://mkennedy.codes/docs/gilguard/)

On a free-threaded build (3.13t, 3.14t, 3.15t), importing an extension module that doesn't declare free-threading support quietly turns the GIL back on for the rest of the process. CPython prints one `RuntimeWarning` and moves on. Once it's on, it can't be turned off.

gilguard turns that into an exception that names the module, the package it came from, and the line of your code that pulled it in.

## Installation

```bash
uv pip install gilguard
```

## Usage

Make it the first import in your program:

```python
import gilguard  # must be first

import fastapi
import pandas  # <- raises here if anything in pandas' import tree needs the GIL
```

```text
gilguard.GILEnabledError: Importing 'gilneeder._speedups' re-enabled the GIL.

  Module:       gilneeder._speedups
  File:         .../site-packages/gilneeder/_speedups.cpython-314t-x86_64-linux-gnu.so
  Distribution: gilneeder 1.2.0
  Import chain: gilneeder -> gilneeder._speedups
  Your code:    /home/me/app.py:5
  Imported by:  .../site-packages/gilneeder/__init__.py:1

This extension module does not declare free-threading support (Py_mod_gil), so CPython turned the GIL back on for the rest of the process. It cannot be turned off again.

Options:
  - Upgrade gilneeder to a release that ships free-threaded (cp314t) wheels.
  - Drop or replace gilneeder.
  - If you have verified it is thread-safe, run with PYTHON_GIL=0 to keep the GIL off (at your own risk).
  - Run `python -m gilguard` to list every installed package that does this.
```

The report is also available as data on `exc.report` (`GILReport`, with `.as_dict()`).

The options at the end of the report are the short version. [Fixing what it finds](https://mkennedy.codes/docs/gilguard/user-guide/fixing-an-offender.html) has the longer one, including how to declare free-threading support in an extension you own.

## What it catches

- Any import that flips the GIL. A `sys.meta_path` finder wraps every loader and checks `sys._is_gil_enabled()` before and after the module is created and executed.
- Imports that bypass `sys.meta_path`, such as `importlib.util.module_from_spec`. gilguard also hooks CPython's own warning to catch these.
- The GIL already being on when gilguard is imported. The report says whether `PYTHON_GIL=1` or `-X gil=1` forced it, or lists the third-party extension modules already loaded as suspects.
- A standard (GIL) build. gilguard raises there, since the GIL is always on.

`GILEnabledError` derives from `BaseException`, not `Exception`. The GIL can't be turned back off, so the common optional-import pattern (`try: import x` / `except ImportError:`) must not be able to swallow it and keep running with the GIL on.

## Imports in worker threads

The error is raised in the thread that ran the import, like any other exception. If that is a worker thread, the thread dies and prints the report, but the main thread keeps running with the GIL on and the process can exit 0. `concurrent.futures` holds the error until you call `.result()`. gilguard does not kill the process for you. If you want a flip in any thread to stop the program, install a `threading.excepthook`:

```python
import os, threading
import gilguard

_prev_hook = threading.excepthook


def _fail_fast(args):
    _prev_hook(args)  # print the report as usual
    if issubclass(args.exc_type, gilguard.GILEnabledError):
        os._exit(1)


threading.excepthook = _fail_fast
```

## What passing means

A clean run means none of the imports that actually ran turned the GIL back on. It does not mean your code or your dependencies are thread-safe, and it does not mean your program gets faster with more threads. Extensions loaded lazily on a code path you didn't exercise aren't checked either.

## Configuration

`GILGUARD_ACTION` environment variable:

| Value | Behavior |
|---|---|
| `raise` (default) | Raise `GILEnabledError` |
| `warn` | Emit `GILGuardWarning` with the same report and keep running |
| `off` | Do nothing (e.g. to run the same code on a standard build) |

Or call `gilguard.install(action=...)` / `gilguard.uninstall()` directly.

`PYTHON_GIL=0` keeps the GIL off no matter what is imported, so gilguard never fires under it.

## Finding every offender

A process can only detect the first module that flips the GIL. After that it's already on. To audit a whole environment, `python -m gilguard` imports each installed top-level package in its own fresh interpreter:

```text
$ python -m gilguard
GIL    gilneeder                via gilneeder._speedups  [gilneeder 1.2.0]

8 checked: 7 ok, 1 re-enable the GIL, 0 failed to import.
```

Pass module names to check specific ones, `--json` for machine-readable output. Exits 1 if any offender is found, so it works as a CI gate. Modules that fail to import on their own are listed as `ERROR` but don't fail the run, since they couldn't be checked. Add `--strict` to fail on those too. Installing gilguard also puts a `gilguard` command on your path that runs the same scan.

Extensions a package loads lazily on first use won't show up in the scan. Run your test suite with gilguard loaded as a plugin to catch those:

```bash
pytest -p gilguard
```

pytest imports `-p` plugins before it collects `conftest.py` or any test module, so the guard is watching before your code imports anything.

## Development

```bash
uv venv -p 3.14t
uv pip install -e . pytest ./tests/fixtures/gilneeder ./tests/fixtures/ftsafe
python -m pytest
```

The fixtures are two tiny C extensions: one without `Py_mod_gil` (re-enables the GIL) and one that declares `Py_MOD_GIL_NOT_USED`.

The docs site is built with [Great Docs](https://posit-dev.github.io/great-docs/) (needs [Quarto](https://quarto.org)). The source is `great-docs.yml`, `index.qmd`, and `user_guide/`. Build it with `python scripts/build_docs.py`, which writes the finished site to `site/` and points its images at the hosted copies. Publish the contents of `site/` to `https://mkennedy.codes/docs/gilguard/`. Use `uvx great-docs preview` for a local preview while writing.
