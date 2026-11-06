# Auditing an environment

Inside a single process, gilguard gets exactly one confession. It catches the first import that turns the GIL on, and after that the GIL is already on, so the next offender has nothing left to flip and walks past unnoticed. That's fine for keeping a running app honest, and no help at all when you want the whole list before you switch an app over.

The scanner gets you the whole list. It gives every installed package its own fresh interpreter, with gilguard loaded first, so no package can hide behind the one that went before it, and reports what each one did.


# Run it

``` bash
python -m gilguard
```

``` text
GIL    gilneeder                via gilneeder._speedups  [gilneeder 1.2.0]

8 checked: 7 ok, 1 re-enable the GIL, 0 failed to import.
Note: only import-time loads are checked. Extensions a package loads lazily on first use will not show up here.
```

Installing gilguard also gives you a `gilguard` command that runs the same scan.

Each `GIL` line gives the package you'd import, the extension module that flips the GIL, and the distribution and version it came from. `ERROR` lines are packages that failed to import on their own. That's often a missing optional dependency. By default it doesn't count against the result, but it also means that package wasn't checked. Pass `--strict` to treat it as a failure.

With no arguments it checks every top-level module of every installed distribution. It skips private names (starting with `_`) and packaging tools such as `pip`, `setuptools` and `wheel`.


# Check specific modules

Pass module names to check just those:

``` bash
python -m gilguard numpy pandas lxml
```

That's quicker than a full scan, and it's how you'd re-check one package after an upgrade to see if the fix took.


# Options

| Option | What it does |
|----|----|
| `--json` | Print the results as JSON instead of the table. |
| `--timeout SECONDS` | Give up on a module after this long. The default is 60. A timeout shows as an error. |
| `-j N`, `--jobs N` | How many modules to check at once. It defaults to your CPU count. |
| `--strict` | Exit 1 when a module fails to import or times out, not only when one re-enables the GIL. |


# JSON output

`--json` returns one entry per module. `status` is `ok`, `gil` or `error`. A `gil` entry includes the full [report](reading-the-report.md), and an `error` entry includes the message:

``` json
{
  "gilneeder": {
    "status": "gil",
    "report": {
      "reason": "import",
      "module": "gilneeder._speedups",
      "distribution": "gilneeder",
      "version": "1.2.0",
      "chain": ["gilneeder", "gilneeder._speedups"],
      ...
    }
  },
  "ftsafe": {
    "status": "ok"
  }
}
```


# Exit codes

| Code | Meaning |
|----|----|
| `0` | No module re-enabled the GIL. Without `--strict`, some may have failed to import and gone unchecked. |
| `1` | At least one did. With `--strict`, also at least one failed to import or timed out. |
| `2` | This isn't a free-threaded interpreter, so there's nothing to scan. |

Because it exits 1 on any offender, the scan works as a CI gate without extra scripting. Use `--strict` in CI if a module that couldn't be checked should fail the build rather than pass quietly. [Tests and CI](tests-and-ci.md) has an example.


# What it can't see

The scan only imports each top-level package. Some packages are shy about their extension modules and load them later, on first use of a feature, and those won't show up. Running your test suite with gilguard active (see [Tests and CI](tests-and-ci.md)) catches those, as long as your tests exercise the code that loads them.

Every child interpreter starts without `PYTHON_GIL` or `GILGUARD_ACTION` set, even if your shell sets them, so the scan reports what each package really does.
