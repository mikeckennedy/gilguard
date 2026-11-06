# API Reference


## When the GIL comes back on


What gilguard raises or warns with, and the report that comes with it.


[GILEnabledError](GILEnabledError.md#gilguard.GILEnabledError)  
The GIL was enabled on a free-threaded interpreter.

[GILReport](GILReport.md#gilguard.GILReport)  
Everything gilguard knows about why the GIL is on.

[GILGuardWarning](GILGuardWarning.md#gilguard.GILGuardWarning)  
Emitted instead of raising when the action is `warn`.


## Turning the guard on and off


`import gilguard` calls install() for you. Use these to choose the action in code or to stop guarding.


[install()](install.md#gilguard.install)  
Start guarding imports.

[uninstall()](uninstall.md#gilguard.uninstall)  
Stop guarding imports.


## Checking the interpreter


Small helpers you can use with or without the guard installed.


[is_free_threaded_build()](is_free_threaded_build.md#gilguard.is_free_threaded_build)  
Check whether this interpreter is a free-threaded build.

[gil_enabled()](gil_enabled.md#gilguard.gil_enabled)  
Check whether the GIL is enabled in this process right now.
