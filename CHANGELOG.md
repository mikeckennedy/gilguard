# Changelog

All notable changes to gilguard are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- `gilguard.install(action='off')` now removes the guard when it is already installed. Before, it only recorded the new action and the hook kept raising, which contradicted the Configuration page.

### Documentation

- New guide page, "Fixing what it finds": upgrade, report upstream, replace, keep going with `warn`, `PYTHON_GIL=0` as a last resort, and how to declare free-threading support in an extension you own.
- A hand-written agent skill (`skills/gilguard/SKILL.md`) replaces the auto-generated one. It carries the rules that matter: first import, `BaseException`, first flip only, what a pass means, and a decision table.
- The docs build now installs gilguard into the Great Docs environment with `GILGUARD_ACTION=off`, so `llms-full.txt` (full API plus the user guide) is generated. It was skipped before, while the skill linked to it.
- Docstrings gained examples, and the module docstring points at the scanner and `pytest -p gilguard`.
- The README mentions the `gilguard` command and recommends `pytest -p gilguard` over an import in `conftest.py`, matching the Tests and CI page.
- The landing page, README and every guide page open with the situation gilguard is for, rather than a definition. The technical content is unchanged.

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

[Unreleased]: https://github.com/mikeckennedy/gilguard/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/mikeckennedy/gilguard/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mikeckennedy/gilguard/releases/tag/v0.1.0
