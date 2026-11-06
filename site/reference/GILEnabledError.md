## GILEnabledError


The GIL was enabled on a free-threaded interpreter.


Usage

``` python
GILEnabledError(report)
```


The message is the formatted report, and the structured version is on `report`.

This derives from `BaseException` on purpose. The GIL can't be turned back off, so an `except Exception:` or `except ImportError:` around an optional import must not be able to swallow it and keep the program running with the GIL on. Catch [gilguard.GILEnabledError](GILEnabledError.md#gilguard.GILEnabledError) by name if you really mean to.


## Parameters


`report: GILReport`  
The details of what turned the GIL on.


## Attributes


`report: GILReport`  
The same report, for code that wants the data rather than the text.
