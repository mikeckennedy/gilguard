"""gilguard - fail loudly when an import re-enables the GIL on free-threaded Python.

Import it first in your program:

    import gilguard  # noqa: F401  (must be the first import)

From then on, any import that turns the GIL back on raises GILEnabledError,
naming the extension module, its file, the distribution that shipped it, the
import chain that pulled it in, and the line of your code that started it.

Environment variable GILGUARD_ACTION controls the behavior:
    raise (default) - raise GILEnabledError
    warn            - emit GILGuardWarning with the same report, keep running
    off             - do nothing
"""

from __future__ import annotations

import os
import re
import sys
import sysconfig
import threading
import warnings
import weakref
from dataclasses import asdict, dataclass, field
from typing import TextIO

__version__ = '0.1.0'
__all__ = [
    'GILEnabledError',
    'GILGuardWarning',
    'GILReport',
    'gil_enabled',
    'install',
    'is_free_threaded_build',
    'uninstall',
]

_CPYTHON_WARNING = 'The global interpreter lock (GIL) has been enabled'
_MODULE_IN_WARNING = re.compile(r"load module '([^']+)'")
_ACTIONS = ('raise', 'warn', 'off')


# --------------------------------------------------------------------------
# Public helpers
# --------------------------------------------------------------------------


def is_free_threaded_build() -> bool:
    """True when this interpreter was built with --disable-gil (python3.13t, 3.14t, ...)."""
    return bool(sysconfig.get_config_var('Py_GIL_DISABLED'))


def gil_enabled() -> bool:
    """True when the GIL is currently enabled in this process."""
    fn = getattr(sys, '_is_gil_enabled', None)
    return True if fn is None else bool(fn())


@dataclass
class GILReport:
    reason: str  # "import", "already-enabled", "gil-build"
    module: str | None = None
    origin: str | None = None
    distribution: str | None = None
    version: str | None = None
    chain: list[str] = field(default_factory=list)
    imported_by: str | None = None  # innermost import statement (inside the package)
    your_code: str | None = None  # outermost import statement (where it started)
    gil_flag: int | None = None  # sys.flags.gil (PYTHON_GIL / -X gil)
    suspects: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def format(self) -> str:
        return _format_report(self)


class GILEnabledError(BaseException):
    """The GIL was enabled on a free-threaded interpreter.

    Derives from BaseException on purpose. The GIL cannot be turned back off,
    so an `except Exception:` or `except ImportError:` around an optional
    import must not be able to swallow this and keep the program running
    with the GIL on.
    """

    def __init__(self, report: GILReport):
        self.report = report
        super().__init__(report.format())


class GILGuardWarning(RuntimeWarning):
    """Emitted instead of raising when GILGUARD_ACTION=warn."""


# --------------------------------------------------------------------------
# Report construction
# --------------------------------------------------------------------------

_THIS_FILE = os.path.normcase(os.path.abspath(__file__))
_STDLIB_DIR = os.path.normcase(os.path.dirname(os.path.abspath(warnings.__file__))) + os.sep
_IMPORTLIB_DIR = _STDLIB_DIR + 'importlib' + os.sep
_WARNINGS_FILES = {_STDLIB_DIR + 'warnings.py', _STDLIB_DIR + '_py_warnings.py'}


def _is_machinery(frame) -> bool:
    fn = frame.f_code.co_filename
    if fn.startswith('<frozen importlib'):
        return True
    norm = os.path.normcase(os.path.abspath(fn)) if not fn.startswith('<') else fn
    return norm == _THIS_FILE or norm.startswith(_IMPORTLIB_DIR) or norm in _WARNINGS_FILES


def _import_sites() -> list[str]:
    """file:line of every import statement on the current stack, outermost first."""
    frames = []
    f = sys._getframe(1)
    while f is not None:
        frames.append(f)
        f = f.f_back
    frames.reverse()
    sites = []
    for outer, inner in zip(frames, frames[1:]):
        if not _is_machinery(outer) and _is_machinery(inner):
            sites.append(f'{outer.f_code.co_filename}:{outer.f_lineno}')
    return sites


def _distribution_for(module: str) -> tuple[str | None, str | None]:
    try:
        from importlib import metadata

        top = module.partition('.')[0]
        dists = metadata.packages_distributions().get(top) or []
        if dists:
            return dists[0], metadata.version(dists[0])
    except Exception:
        pass
    return None, None


def _build_import_report(module: str, origin: str | None, chain: list[str]) -> GILReport:
    dist, version = _distribution_for(module)
    sites = _import_sites()
    return GILReport(
        reason='import',
        module=module,
        origin=origin,
        distribution=dist,
        version=version,
        chain=chain,
        imported_by=sites[-1] if sites else None,
        your_code=sites[0] if sites else None,
        gil_flag=getattr(sys.flags, 'gil', None),
    )


def _loaded_third_party_extensions() -> list[str]:
    from importlib.machinery import EXTENSION_SUFFIXES

    paths = sysconfig.get_paths()
    std = tuple(os.path.normcase(os.path.abspath(paths[k])) for k in ('stdlib', 'platstdlib'))
    site_dirs = tuple(os.path.normcase(os.path.abspath(paths[k])) for k in ('purelib', 'platlib'))
    out = []
    for name, mod in list(sys.modules.items()):
        origin = getattr(getattr(mod, '__spec__', None), 'origin', None)
        if not origin or not origin.endswith(tuple(EXTENSION_SUFFIXES)):
            continue
        norm = os.path.normcase(os.path.abspath(origin))
        if norm.startswith(std) and not norm.startswith(site_dirs):
            continue
        out.append(name)
    return sorted(out)


def _format_report(r: GILReport) -> str:
    ft_tag = f'cp{sys.version_info.major}{sys.version_info.minor}t'

    if r.reason == 'gil-build':
        return (
            'This is not a free-threaded Python build, so the GIL is always on.\n\n'
            f'  Interpreter: {sys.executable} ({sys.version.split()[0]})\n\n'
            'Run with a free-threaded interpreter instead (for example python3.14t, or `uv python install 3.14t`).\n'
            'Set GILGUARD_ACTION=off to allow running on a standard build.'
        )

    if r.reason == 'already-enabled':
        lines = ['The GIL was already enabled before gilguard was imported.', '']
        if r.gil_flag == 1:
            lines.append('  Cause: the GIL was forced on with PYTHON_GIL=1 or -X gil=1.')
        elif r.suspects:
            lines.append('  Third-party extension modules already loaded (one of these turned it on):')
            lines.extend(f'    - {s}' for s in r.suspects)
        else:
            lines.append(
                '  Something imported before gilguard (sitecustomize, a .pth file, or an earlier import) turned it on.'
            )
        lines += ['', 'Make `import gilguard` the very first import in your program.']
        return '\n'.join(lines)

    dist = f'{r.distribution} {r.version}' if r.distribution else '(unknown - not from an installed distribution)'
    rows = [
        ('Module', r.module),
        ('File', r.origin or '(unknown)'),
        ('Distribution', dist),
        ('Import chain', ' -> '.join(r.chain) if r.chain else r.module),
    ]
    if r.your_code:
        rows.append(('Your code', r.your_code))
    if r.imported_by and r.imported_by != r.your_code:
        rows.append(('Imported by', r.imported_by))

    width = max(len(k) for k, _ in rows) + 1
    lines = [f"Importing '{r.module}' re-enabled the GIL.", '']
    lines += [f'  {k + ":":<{width}} {v}' for k, v in rows]
    pkg = r.distribution or (r.module or '?').partition('.')[0]
    lines += [
        '',
        'This extension module does not declare free-threading support (Py_mod_gil), so CPython turned the GIL '
        'back on for the rest of the process. It cannot be turned off again.',
        '',
        'Options:',
        f'  - Upgrade {pkg} to a release that ships free-threaded ({ft_tag}) wheels.',
        f'  - Drop or replace {pkg}.',
        '  - If you have verified it is thread-safe, run with PYTHON_GIL=0 to keep the GIL off (at your own risk).',
        '  - Run `python -m gilguard` to list every installed package that does this.',
    ]
    return '\n'.join(lines)


# --------------------------------------------------------------------------
# Import hook
# --------------------------------------------------------------------------

_installed = False
_action = 'raise'
_reported = False
_report_lock = threading.Lock()
_state = threading.local()
_orig_showwarning = warnings.showwarning  # replaced with the live hook when install() runs
_finder: _GILGuardFinder | None = None
_guarded: weakref.WeakSet = weakref.WeakSet()  # loader methods _wrap() has already replaced


def _stack() -> list[tuple[str, str | None]]:
    s = getattr(_state, 'stack', None)
    if s is None:
        s = _state.stack = []
    return s


def _handle(report: GILReport) -> None:
    """Raise or warn for a detected flip. Only the first flip is reported."""
    global _reported
    with _report_lock:
        if _reported:
            return
        _reported = True
    if _action == 'warn':
        warnings.warn(report.format(), GILGuardWarning, stacklevel=2)
        return
    raise GILEnabledError(report)


def _report_from_stack(module: str) -> GILReport:
    stack = _stack()
    chain = [name for name, _ in stack]
    origin = None
    if stack and stack[-1][0] == module:
        origin = stack[-1][1]
    else:
        chain.append(module)
    return _build_import_report(module, origin, chain)


def _wrap(method, get_name_origin):
    def guarded(arg):
        if not _installed or gil_enabled():
            return method(arg)
        name, origin = get_name_origin(arg)
        stack = _stack()
        stack.append((name, origin))
        try:
            result = method(arg)
            if gil_enabled():
                _handle(_report_from_stack(name))
            return result
        except GILEnabledError:
            raise
        except BaseException:
            if gil_enabled():
                _handle(_report_from_stack(name))
            raise
        finally:
            stack.pop()

    _guarded.add(guarded)
    return guarded


def _from_spec(spec):
    return spec.name, spec.origin


def _from_module(module):
    spec = getattr(module, '__spec__', None)
    return getattr(module, '__name__', '?'), getattr(spec, 'origin', None)


class _GILGuardFinder:
    """Delegates to the rest of sys.meta_path and wraps the loader it gets back."""

    def find_spec(self, name, path=None, target=None):
        for finder in sys.meta_path:
            if finder is self:
                continue
            find = getattr(finder, 'find_spec', None)
            if find is None:
                continue
            spec = find(name, path, target)
            if spec is not None:
                _instrument(spec.loader)
                return spec
        return None

    def invalidate_caches(self):
        pass


def _instrument(loader) -> None:
    # BuiltinImporter / FrozenImporter are classes shared by every built-in module; leave them alone.
    if loader is None or isinstance(loader, type):
        return
    for attr, extract in (('create_module', _from_spec), ('exec_module', _from_module)):
        method = getattr(loader, attr, None)
        if method is None or method in _guarded:
            continue
        try:
            setattr(loader, attr, _wrap(method, extract))
        except (AttributeError, TypeError):
            pass  # loader with __slots__ etc. - the warning backstop still covers it


def _showwarning(
    message: Warning | str,
    category: type[Warning],
    filename: str,
    lineno: int,
    file: TextIO | None = None,
    line: str | None = None,
) -> None:
    # Backstop: CPython emits this warning at the moment it flips the GIL. It catches
    # imports that bypass sys.meta_path (e.g. importlib.util.module_from_spec).
    text = str(message)
    if _installed and issubclass(category, RuntimeWarning) and text.startswith(_CPYTHON_WARNING):
        m = _MODULE_IN_WARNING.search(text)
        module = m.group(1) if m else '?'
        stack = _stack()
        if stack and stack[-1][0] == module:
            return  # inside our wrapper: it raises right after create_module returns, with a cleaner traceback
        _handle(_report_from_stack(module))
        return
    return _orig_showwarning(message, category, filename, lineno, file, line)


def install(action: str | None = None) -> None:
    """Start guarding imports. Called automatically when gilguard is imported."""
    global _installed, _action, _orig_showwarning, _finder

    action = (action or os.environ.get('GILGUARD_ACTION') or 'raise').strip().lower()
    if action not in _ACTIONS:
        raise ValueError(f'GILGUARD_ACTION must be one of {", ".join(_ACTIONS)}, got {action!r}')
    _action = action
    if action == 'off' or _installed:
        return

    if not is_free_threaded_build():
        _handle(GILReport(reason='gil-build'))
        return

    if gil_enabled():
        _handle(
            GILReport(
                reason='already-enabled',
                gil_flag=getattr(sys.flags, 'gil', None),
                suspects=_loaded_third_party_extensions(),
            )
        )
        return

    _finder = _GILGuardFinder()
    sys.meta_path.insert(0, _finder)
    _orig_showwarning = warnings.showwarning
    # Replacing showwarning is the documented hook, but typeshed declares it as a def,
    # so ty only accepts that exact function there.
    warnings.showwarning = _showwarning  # ty: ignore[invalid-assignment]
    warnings.filterwarnings('always', message=re.escape(_CPYTHON_WARNING), category=RuntimeWarning)
    _installed = True


def uninstall() -> None:
    """Stop guarding imports."""
    global _installed
    if not _installed:
        return
    _installed = False
    if _finder is not None and _finder in sys.meta_path:
        sys.meta_path.remove(_finder)
    if warnings.showwarning is _showwarning:
        warnings.showwarning = _orig_showwarning


install()
