# Configuration

gilguard has one dial: what to do when the GIL comes on. You set it with an environment variable or in code.


# GILGUARD_ACTION

| Value | What happens |
|----|----|
| `raise` (default) | Raise [GILEnabledError](../reference/GILEnabledError.md#gilguard.GILEnabledError) at the import that did it. |
| `warn` | Emit [GILGuardWarning](../reference/GILGuardWarning.md#gilguard.GILGuardWarning) with the same report and keep running. |
| `off` | Don't install the guard at all. |

``` bash
GILGUARD_ACTION=warn python app.py
```

The value isn't case sensitive. Anything other than those three raises `ValueError` when gilguard is imported, so a typo fails fast instead of quietly turning the guard off.


## When to use warn

`warn` suits a first pass over an existing app. Every report lands in your logs, nothing goes down, and once the list is empty you switch to `raise` so it stays empty. The warning is a [GILGuardWarning](../reference/GILGuardWarning.md#gilguard.GILGuardWarning), a `RuntimeWarning` subclass, so your existing warning filters and logging capture it like any other.

Remember that in warn mode the program keeps running with the GIL on. It's a way to find problems, not a way to live with them.


## When to use off

`off` is for running the same code on a standard GIL build, where gilguard would otherwise raise because the GIL is always on. Set it in the environments that use a standard build and leave it unset where you run free-threaded.


# In code

[install()](../reference/install.md#gilguard.install) takes the same values and wins over the environment variable:

``` python
import gilguard

gilguard.install(action='warn')
```

`import gilguard` already called [install()](../reference/install.md#gilguard.install), and a second call doesn't add another hook. It just changes the action, and `install(action='off')` removes the hook, the same as [uninstall()](../reference/uninstall.md#gilguard.uninstall). If you need a specific action from the very first import, use the environment variable. Otherwise anything imported before your [install()](../reference/install.md#gilguard.install) call runs under the default.

[uninstall()](../reference/uninstall.md#gilguard.uninstall) removes the hook. Imports after that can turn the GIL on without a report. Call [install()](../reference/install.md#gilguard.install) again to resume.

``` python
gilguard.uninstall()
import legacy_thing  # unguarded

gilguard.install()
```


# PYTHON_GIL

CPython's own `PYTHON_GIL` environment variable (or `-X gil=`) takes priority over everything above:

- `PYTHON_GIL=0` keeps the GIL off no matter what gets imported. Nothing ever flips, so gilguard never fires. Use it only for extensions you've checked are thread-safe even though they don't declare it.
- `PYTHON_GIL=1` forces the GIL on from the start. gilguard sees that when it's imported and reports it as the cause.


# Helpers

Two small functions are handy whether or not the guard is installed:

``` python
gilguard.is_free_threaded_build()  # True on a 't' build
gilguard.gil_enabled()  # True if the GIL is on right now
```

They answer different questions, and the gap between them is exactly where gilguard lives: a free-threaded build with the GIL on.
