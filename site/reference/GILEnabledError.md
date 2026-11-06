## GILEnabledError


The GIL was enabled on a free-threaded interpreter.


Usage

``` python
GILEnabledError(report)
```


The message is the formatted report, and the structured version is on `report`.

This derives from `BaseException` on purpose. The GIL can't be turned back off, so an `except Exception:` or `except ImportError:` around an optional import must not be able to swallow it and keep the program running with the GIL on. Catch [gilguard.GILEnabledError](GILEnabledError.md#gilguard.GILEnabledError) by name if you really mean to.

It is raised in the thread that ran the import. In a worker thread, that thread dies but the rest of the process keeps running with the GIL on. Install a `threading.excepthook` if you want any flip to end the program.


## Parameters


`report: GILReport`  
The details of what turned the GIL on.


## Attributes


`report: GILReport`  
The same report, for code that wants the data rather than the text.
