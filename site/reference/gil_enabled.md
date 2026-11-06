## gil_enabled()


Check whether the GIL is enabled in this process right now.


Usage

``` python
gil_enabled()
```


On a free-threaded build this starts out `False` and flips to `True` for good once something turns the GIL back on. On a standard build it is always `True`.


## Returns


`bool`  
`True` if the GIL is currently enabled.
