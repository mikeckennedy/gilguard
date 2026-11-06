## is_free_threaded_build()


Check whether this interpreter is a free-threaded build.


Usage

``` python
is_free_threaded_build()
```


A free-threaded build is one compiled with `--disable-gil`, usually installed as `python3.13t`, `python3.14t` and so on. This says nothing about whether the GIL is on right now; use [gil_enabled()](gil_enabled.md#gilguard.gil_enabled) for that.


## Returns


`bool`  
`True` on a free-threaded build, `False` on a standard build.
