# Reading the report

Every [GILEnabledError](../reference/GILEnabledError.md#gilguard.GILEnabledError) carries a [GILReport](../reference/GILReport.md#gilguard.GILReport). The exception message is the report rendered as text. `exc.report` is the same thing as data.


# The import report

This is the one you'll see most. An import just turned the GIL on:

``` text
gilguard.GILEnabledError: Importing 'gilneeder._speedups' re-enabled the GIL.

  Module:       gilneeder._speedups
  File:         .../site-packages/gilneeder/_speedups.cpython-314t-x86_64-linux-gnu.so
  Distribution: gilneeder 1.2.0
  Import chain: gilneeder -> gilneeder._speedups
  Your code:    /home/me/app.py:5
  Imported by:  .../site-packages/gilneeder/__init__.py:1
```

Here's what each line tells you:


Module  
The extension module that doesn't declare free-threading support. This is the thing that actually flipped the GIL.

File  
Where that module lives. The filename shows the ABI it was built for. A `cp314t` tag means a free-threaded wheel was installed and the module just doesn't declare support yet.

Distribution  
The installed package that shipped the module, and its version. This is what you'd upgrade, pin or replace.

Import chain  
Every module on the way down, starting with the one your code imported. Useful when the offender is a dependency of a dependency.

Your code  
The import statement where the chain started, usually in your own code.

Imported by  
The statement that loaded the offending module, usually inside the package. It's left out when it's the same line as "Your code".


If gilguard can't match the module to an installed distribution (it's on `sys.path` from a source checkout, say), the Distribution line says so.

After the details, the report lists your options: upgrade to a release with free-threaded wheels, drop or replace the package, or, if you've confirmed it's thread-safe, run with `PYTHON_GIL=0` to keep the GIL off anyway.


# Two other reasons

The GIL can also be on before gilguard gets a chance to watch.

**It was already on when gilguard was imported.** If the GIL was forced on, the report says so:

``` text
gilguard.GILEnabledError: The GIL was already enabled before gilguard was imported.

  Cause: the GIL was forced on with PYTHON_GIL=1 or -X gil=1.

Make `import gilguard` the very first import in your program.
```

Otherwise gilguard lists the third-party extension modules that were already loaded. One of them did it:

``` text
gilguard.GILEnabledError: The GIL was already enabled before gilguard was imported.

  Third-party extension modules already loaded (one of these turned it on):
    - gilneeder._speedups

Make `import gilguard` the very first import in your program.
```

If that list is empty, something ran before your code did: a `sitecustomize` module or a `.pth` file are the usual suspects.

**It's a standard build.** The GIL is always on, so gilguard raises with the interpreter path and a pointer to `GILGUARD_ACTION=off`.


# Using the report in code

The same fields are on `exc.report`, and [as_dict()](../reference/GILReport.md#gilguard.GILReport.as_dict) gives you something you can serialize:

``` python
import json
import gilguard

try:
    import gilneeder
except gilguard.GILEnabledError as e:
    print(json.dumps(e.report.as_dict(), indent=2))
    raise
```

``` json
{
  "reason": "import",
  "module": "gilneeder._speedups",
  "origin": ".../site-packages/gilneeder/_speedups.cpython-315t-darwin.so",
  "distribution": "gilneeder",
  "version": "1.2.0",
  "chain": ["gilneeder", "gilneeder._speedups"],
  "imported_by": ".../site-packages/gilneeder/__init__.py:1",
  "your_code": "app.py:4",
  "gil_flag": null,
  "suspects": []
}
```

`reason` is `"import"`, `"already-enabled"` or `"gil-build"`, and tells you which of the other fields are filled in. The [`GILReport` reference](../reference/GILReport.md) describes each field.

> **Note: Re-raise if you catch it**
>
> Catching [GILEnabledError](../reference/GILEnabledError.md#gilguard.GILEnabledError) doesn't put things back. The GIL is on for the rest of the process either way. Catch it to log or report, then let it go.


# Only the first one

gilguard reports the first import that turns the GIL on and stays quiet after that. Once it's on, later imports can't turn it on again, so there's nothing more to catch in that process. To find every offender, use [`python -m gilguard`](auditing-an-environment.md), which gives each package its own interpreter.
