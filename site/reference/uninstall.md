## uninstall()


Stop guarding imports.


Usage

``` python
uninstall()
```


This removes gilguard's import hook and restores `warnings.showwarning`. Later imports can turn the GIL on without a report. Call [install()](install.md#gilguard.install) to start guarding again.
