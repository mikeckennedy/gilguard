## GILReport


Everything gilguard knows about why the GIL is on.


Usage

``` python
GILReport(
    reason,
    module=None,
    origin=None,
    distribution=None,
    version=None,
    chain=list(),
    imported_by=None,
    your_code=None,
    gil_flag=None,
    suspects=list()
)
```


You get one of these as `GILEnabledError.report`. Which fields are filled in depends on `reason`: an import flip fills in the module details, while the other two reasons only describe the interpreter.


## Attributes


`reason: str`  
What happened. `"import"` means an import turned the GIL on. `"already-enabled"` means it was on before gilguard was imported. `"gil-build"` means this is a standard build, where the GIL is always on.

`module: str | None`  
Full name of the extension module that turned the GIL on, such as `"gilneeder._speedups"`.

`origin: str | None`  
Path to that module's file, usually a `.so` or `.pyd`.

`distribution: str | None`  
Name of the installed distribution that shipped the module, if gilguard can find one.

`version: str | None`  
Version of that distribution.

`chain: list[str]`  
Module names from the first import down to the offender, outermost first. `["pandas", "pandas._libs", "pandas._libs.lib"]` reads as "pandas imported pandas.\_libs, which imported pandas.\_libs.lib".

`imported_by: str | None`  
`file:line` of the innermost import statement, the one that loaded the offending module. This is usually inside the package itself.

`your_code: str | None`  
`file:line` of the outermost import statement, where the chain started. This is usually your code.

`gil_flag: int | None`  
The value of `sys.flags.gil`: `1` when `PYTHON_GIL=1` or `-X gil=1` forced the GIL on, `0` when it was forced off, `None` when neither was set.

`suspects: list[str]`  
For `"already-enabled"`, the third-party extension modules that were already loaded. One of them turned the GIL on.


## Methods

| Name | Description |
|----|----|
| [as_dict()](#as_dict) | Return the report as a plain dict, ready for `json.dumps()`. |
| [format()](#format) | Render the report as the human-readable text gilguard prints. |

------------------------------------------------------------------------


#### as_dict()


Return the report as a plain dict, ready for `json.dumps()`.


Usage

``` python
as_dict()
```


##### Returns


`dict`  
One key per attribute, with the same names.


------------------------------------------------------------------------


#### format()


Render the report as the human-readable text gilguard prints.


Usage

``` python
format()
```


This is the same text you see in the [GILEnabledError](GILEnabledError.md#gilguard.GILEnabledError) message and the [GILGuardWarning](GILGuardWarning.md#gilguard.GILGuardWarning).


##### Returns


`str`  
A multi-line description of what happened and how to fix it.
