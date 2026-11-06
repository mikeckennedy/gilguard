## install()


Start guarding imports.


Usage

``` python
install(action=None)
```


`import gilguard` calls this for you, so you only need it to choose the action in code, or to start guarding again after [uninstall()](uninstall.md#gilguard.uninstall).

Before it starts guarding, it checks the interpreter. On a standard build, or if the GIL is already on, it reports that straight away instead.


## Parameters


`action: str | None = None`  
`"raise"` to raise [GILEnabledError](GILEnabledError.md#gilguard.GILEnabledError), `"warn"` to emit [GILGuardWarning](GILGuardWarning.md#gilguard.GILGuardWarning) and keep running, or `"off"` to do nothing. `None` reads the `GILGUARD_ACTION` environment variable and falls back to `"raise"`.


## Raises


`ValueError`  
If the action is not one of `raise`, `warn` or `off`.

`GILEnabledError`  
If the action is `raise` and the interpreter is a standard build, or the GIL is already enabled.
