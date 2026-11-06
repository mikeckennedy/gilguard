# Getting started


# The problem gilguard solves

Think of a free-threaded build (the `t` builds: `3.13t`, `3.14t`, `3.15t`) as running on a contract. The interpreter agrees to run without the global interpreter lock, so threads can execute Python code at the same time. In return, every extension module that loads has to sign: a C extension declares that it's safe without the GIL by setting the `Py_mod_gil` slot. The first module that loads without a signature voids the contract for everyone. CPython plays safe and switches the GIL back on for the whole process, for the rest of its life.

It tells you with a single line:

``` text
RuntimeWarning: The global interpreter lock (GIL) has been enabled to load module
'gilneeder._speedups', which has not declared that it can run safely without the GIL.
```

That's easy to miss in a busy log, and it names only the extension module, not the package you installed or the line that imported it. The program keeps working, just without the parallelism you switched builds for. You can run like that for weeks and never know.

gilguard makes that moment loud, immediate, and specific.


# Install

``` bash
uv pip install gilguard
```

Plain `pip install gilguard` works too. gilguard has no dependencies and needs Python 3.13 or newer. To be useful it has to run on a free-threaded interpreter. If you don't have one yet:

``` bash
uv python install 3.14t
uv venv -p 3.14t
```


# Make it the first import

``` python
import gilguard  # must be first

import fastapi
import pandas
```

Importing gilguard installs the guard. There's nothing to call and nothing to configure. From then on, any import that turns the GIL on raises [GILEnabledError](../reference/GILEnabledError.md#gilguard.GILEnabledError) at that import statement, with a [report](reading-the-report.md) of what happened.

It has to come first for the same reason a tripwire goes across the doorway: gilguard can only watch imports that happen after it. If something earlier has already turned the GIL on, gilguard notices the moment it's imported and raises straight away, listing the extension modules already loaded. One of them is the culprit.

> **Tip: Where "first" is in your app**
>
> Put it at the top of whatever module starts your process: `main.py`, the module your ASGI server loads, `manage.py`, or `__main__.py`. For tests, see [Tests and CI](tests-and-ci.md). There's a better spot than `conftest.py`.


# Try it

The fastest way to find out what's lurking in your environment is the scanner:

``` bash
python -m gilguard
```

``` text
GIL    gilneeder                via gilneeder._speedups  [gilneeder 1.2.0]

8 checked: 7 ok, 1 re-enable the GIL, 0 failed to import.
```

Each package gets imported in its own interpreter, so one offender can't hide the rest. [Auditing an environment](auditing-an-environment.md) covers the options.


# On a standard build

On a regular GIL build there's nothing to guard. The GIL is on, it has always been on, and gilguard says so by raising:

``` text
gilguard.GILEnabledError: This is not a free-threaded Python build, so the GIL is always on.
```

If the same code has to run on both kinds of build, set `GILGUARD_ACTION=off` wherever it runs with the GIL. [Configuration](configuration.md) has the details.
