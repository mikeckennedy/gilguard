# Fixing what it finds

You have a name. The report says which extension module turned the GIL on and which distribution shipped it, and that's most of the detective work done. This page is about what to do with the name. The options are in rough order of effort, so start at the top and stop when one works.


# Upgrade the distribution

Most offenders are packages whose maintainers have already done the work, just not in the version you have pinned. Upgrade and ask again:

``` bash
uv pip install --upgrade gilneeder
python -m gilguard gilneeder
```

The wheel filename tells you what you got. A free-threaded wheel carries a `t` in its ABI tag, such as `cp314t`, and the `File` line of the report shows the same tag in the module's filename. If the package has no `t` wheels for your platform, pip or uv built it from source, and nothing in that build declares free-threading support unless the package's own code does.

The [free-threading compatibility tracker](https://py-free-threading.github.io/tracking/) lists where popular packages with native code stand, and usually links the release or issue that added support.

> **Note: A `t` wheel is necessary, not sufficient**
>
> A wheel built for the free-threaded ABI can still contain extension modules that don't declare `Py_mod_gil`. Those turn the GIL on when they load, same as any other. The report names the exact module, which is what the maintainers need to hear about.


# Report it upstream

If the latest release still flips the GIL, the project may not know, or may know but not which of its modules does it. A package can ship dozens of extension modules, and the one that matters is often a private helper nobody has looked at in years. Open an issue with the report's `Module`, `File` and `Distribution` lines and your Python version. The `Import chain` line helps too, since it shows how the module gets loaded.

For maintainers, the community [porting guide for extension modules](https://py-free-threading.github.io/porting-extensions/) and CPython's [free-threading HOWTO](https://docs.python.org/3/howto/free-threading-extensions.html) cover what's involved.


# Replace or drop it

If upgrading isn't an option, find out who needs the package. The `Your code` line is where the chain started, which may be a direct import or a dependency you never named. `uv pip tree` or `pipdeptree` shows what depends on it. Then swap in a package with free-threaded wheels, or drop the feature that needs it.


# Keep running while you wait

If you can't fix it today but want the app on a free-threaded build anyway, set `GILGUARD_ACTION=warn`. The program keeps running with the GIL on, the same report lands in your logs, and you still find out the day a new dependency starts doing the same thing. It's a holding pattern, not a destination. Switch back to `raise` once the list is empty. [Configuration](configuration.md) covers the modes.


# Last resort: PYTHON_GIL=0

`PYTHON_GIL=0` tells CPython to keep the GIL off even when a module doesn't declare support. The missing declaration might be an oversight, or the module might rely on the GIL for correctness, and the only way to know is to ask the maintainers or read the code. If it's the latter, you've traded an error you can read for data races you can't. gilguard never fires under `PYTHON_GIL=0` because the GIL never comes on, so you also lose the guard for every other package. Use it to test one package you've checked, not as the way you run production.


# If the extension is yours

Declaring support is one slot, and that one slot is the entire difference between gilguard's two test fixtures. `gilneeder` uses single-phase initialization and declares nothing, so it turns the GIL on. `ftsafe` uses multi-phase initialization and adds the slot:

``` c
static PyModuleDef_Slot slots[] = {
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {0, NULL},
};
```

That works with multi-phase initialization (`PyModuleDef_Init`). With single-phase initialization (`PyModule_Create`), call `PyUnstable_Module_SetGIL(m, Py_MOD_GIL_NOT_USED)` on the module before returning it, inside `#ifdef Py_GIL_DISABLED`, since that function only exists on free-threaded builds. The slot itself exists on every 3.13+ build, so it only needs a `PY_VERSION_HEX` guard if you still compile for 3.12 or older.

The binding tools each have their own switch:

| Tool | How to declare |
|----|----|
| Cython 3.1+ | `# cython: freethreading_compatible = True` at the top of the `.pyx` |
| pybind11 2.13+ | `PYBIND11_MODULE(name, m, py::mod_gil_not_used())` |
| PyO3 0.23+ | `#[pymodule(gil_used = false)]` |

> **Warning: The declaration is a promise**
>
> `Py_MOD_GIL_NOT_USED` tells CPython your module is safe to run without the GIL. It doesn't make it safe. Global state, caches, and anything the GIL used to serialize for you need a look first. CPython's [free-threading HOWTO](https://docs.python.org/3/howto/free-threading-extensions.html) lists what to check.

Then build a free-threaded wheel, install it, and confirm with `python -m gilguard yourpackage`.
