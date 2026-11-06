## GILGuardWarning


Emitted instead of raising when the action is `warn`.


Usage

``` python
GILGuardWarning()
```


The warning message is the same formatted report that [GILEnabledError](GILEnabledError.md#gilguard.GILEnabledError) carries. It subclasses `RuntimeWarning`, so you can filter it, log it or capture it like any other warning.
