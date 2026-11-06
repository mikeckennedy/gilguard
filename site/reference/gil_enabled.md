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


## Examples

A free-threaded build can still have the GIL on. That is the case gilguard exists for, and this is how to check for it by hand:

``` python
import gilguard

assert gilguard.is_free_threaded_build()
assert not gilguard.gil_enabled(), 'something already turned the GIL on'
```
