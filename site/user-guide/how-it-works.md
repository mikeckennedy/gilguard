# How it works

gilguard is one module of plain Python, a few hundred lines with no dependencies. You don't need any of this to use it, but it helps to know what it's doing when you read a report.


# Watching every import

When you import gilguard, it puts a finder at the front of `sys.meta_path`. That finder doesn't find anything itself. For each import, it asks the rest of `sys.meta_path` who can load the module, then wraps that loader's `create_module` and `exec_module` before handing it back.

The wrapped methods check `sys._is_gil_enabled()` before and after they run. If the GIL was off before and is on after, that module turned it on. gilguard builds the report on the spot, while the import is still on the stack.

That timing is what makes the report specific. While an import is in progress, gilguard keeps track of which modules are loading inside which (the import chain), and it walks the Python stack to find the import statements involved. The outermost one outside the import machinery is "Your code". The innermost is "Imported by".

The chain is tracked per thread, so imports running at the same time on different threads each get their own chain.


# The backstop

Some code loads modules without going through `sys.meta_path`. `importlib.util.module_from_spec()` with a hand-built spec is the common case. Those imports never reach the finder.

CPython always emits its `RuntimeWarning` at the moment it turns the GIL on, however the module was loaded. gilguard installs its own `warnings.showwarning`, recognizes that one warning, and reports from there. Every other warning passes through to the original handler untouched.

When an import goes through the finder, the warning still fires, but gilguard ignores it and lets the wrapper raise a moment later. That gives you a cleaner traceback that ends at your import statement.


# Why BaseException

[GILEnabledError](../reference/GILEnabledError.md#gilguard.GILEnabledError) derives from `BaseException`, the same as `KeyboardInterrupt` and `SystemExit`. That's deliberate. Optional imports in the wild look like this:

``` python
try:
    import fastjson as json
except ImportError:
    import json
```

If the error were an `ImportError`, or any `Exception`, that pattern would catch it, fall back, and keep running with the GIL already on. Nothing would be fixed and nothing would be reported. Because [GILEnabledError](../reference/GILEnabledError.md#gilguard.GILEnabledError) sits outside `Exception`, only code that names it explicitly can catch it.


# First flip only

gilguard reports once per process. Once the GIL is on, nothing turns it off, and no later import can turn it on again, so there's nothing left to report. It's also why the [scanner](auditing-an-environment.md) needs a separate interpreter for each package.


# When it checks the interpreter

At import time, before installing anything, gilguard checks two things. Is this a free-threaded build? If not, it reports `gil-build`. Is the GIL already on? If so, it reports `already-enabled`, with `sys.flags.gil` to show whether it was forced, plus the third-party extension modules already in `sys.modules` as suspects. Only after both checks pass does it install the finder and the warning hook.
