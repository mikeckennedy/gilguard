---
name: gilguard
description: >
  Raise a detailed error the moment an import re-enables the GIL on free-threaded Python. Use when writing Python code that uses the gilguard package.
license: MIT
compatibility: Requires Python >=3.13.
---

# gilguard

Raise a detailed error the moment an import re-enables the GIL on free-threaded Python.

## Installation

```bash
pip install gilguard
```

## API overview

### When the GIL comes back on

What gilguard raises or warns with, and the report that comes with it.

- `GILEnabledError`
- `GILReport`
- `GILGuardWarning`

### Turning the guard on and off

`import gilguard` calls install() for you. Use these to choose the action in code or to stop guarding.

- `install`
- `uninstall`

### Checking the interpreter

Small helpers you can use with or without the guard installed.

- `is_free_threaded_build`
- `gil_enabled`

## Resources

- [Full documentation](https://mkennedy.codes/docs/gilguard/)
- [llms.txt](llms.txt) — Indexed API reference for LLMs
- [llms-full.txt](llms-full.txt) — Comprehensive documentation for LLMs
- [Source code](https://github.com/mikeckennedy/gilguard)
