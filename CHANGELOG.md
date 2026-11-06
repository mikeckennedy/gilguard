# Changelog

All notable changes to gilguard are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-05

### Added

- `python -m gilguard --strict` exits 1 when a module fails to import or times out, not only when one re-enables the GIL. Without it, a module that couldn't be imported was never checked but still left the exit code at 0.
- The scanner's text output now notes when modules failed to import and went unchecked, and points to `--strict`.

### Documentation

- Explain that `GILEnabledError` is raised only in the thread that ran the import. A flip in a worker thread kills that thread, while the rest of the process keeps running with the GIL on and can exit 0. The docs include an opt-in `threading.excepthook` recipe for stopping the whole program.
- State what a passing run means: the imports that ran kept the GIL off. It does not prove thread safety or a speedup from threads.
- The CI example now runs the scan with `--strict`.

## [0.1.0] - 2026-11-05

### Added

- First release. `import gilguard` raises `GILEnabledError` when an import re-enables the GIL on free-threaded Python, naming the module, distribution, import chain, and the line of your code that started it.
- `GILGUARD_ACTION` (`raise`, `warn`, `off`) and `install()` / `uninstall()`.
- Reports for a GIL that was already on before gilguard loaded, and for standard GIL builds.
- `python -m gilguard` scans every installed package in a fresh interpreter each.

[0.2.0]: https://github.com/mikeckennedy/gilguard/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mikeckennedy/gilguard/releases/tag/v0.1.0
