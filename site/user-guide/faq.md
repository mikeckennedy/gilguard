# FAQ


# Does gilguard slow down imports?

Not noticeably. It adds a wrapper around each loader and a couple of `sys._is_gil_enabled()` calls per module. That's tiny next to the work of finding and executing a module. It adds nothing after imports finish.


# Can I just catch GILEnabledError and carry on?

You can, by naming it in an `except`, but it doesn't help. The GIL stays on for the rest of the process either way. If you want the program to keep running while you collect reports, use `GILGUARD_ACTION=warn`. That's what it's for.


# A package ships cp314t wheels. Why is it flagged?

A free-threaded wheel means the package was compiled for the free-threaded ABI. It doesn't mean every extension module in it declares `Py_mod_gil`. Some projects publish `t` wheels before they've audited everything, and those modules still turn the GIL on when they load. The report names the specific module, which is useful in a bug report to the project.


# Should I run with PYTHON_GIL=0 to make the error go away?

Only for extensions you've confirmed are thread-safe. `PYTHON_GIL=0` makes CPython ignore the missing declaration and keep the GIL off. If the extension really does rely on the GIL, you get data races instead of an error. gilguard never fires under `PYTHON_GIL=0`, because the GIL never comes on.


# Does it work on Python 3.13?

Yes, on `3.13t`. gilguard supports 3.13 and later, including `3.14t` and `3.15t`. On any standard build it raises at import unless you set `GILGUARD_ACTION=off`.


# Why didn't the scanner find a package my app trips on?

The scanner imports each top-level package and nothing else. If the package loads an extension later, when you call a particular function, the scan can't see it. Run your tests with `pytest -p gilguard` to cover those code paths. See [Tests and CI](tests-and-ci.md).


# Can I use it in production?

Yes. It's a pure-Python import hook with no dependencies. In `raise` mode, a deploy that pulls in an offending package fails at startup with a clear report, instead of running for weeks with the GIL quietly on. If you'd rather never fail a request over it, use `warn` and alert on the warning.
