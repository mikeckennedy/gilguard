"""Build the docs site into ./site.

Runs Great Docs, copies its output (great-docs/_site, which is ignored) to ./site,
and points every image at the hosted copies so ./site carries no image files of its own.

Great Docs only accepts a local file for the navbar logo (it copies it and builds
the favicons from it), so the HTML is rewritten after the build.

Usage:
    python scripts/build_docs.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'great-docs' / '_site'
SITE = ROOT / 'site'

CDN = 'https://mkennedy-shared.nyc3.digitaloceanspaces.com/github'
LOGO_LIGHT = f'{CDN}/gilguard-logo-light.png'
LOGO_DARK = f'{CDN}/gilguard-logo-dark.png'

# Copies Great Docs drops into the output that the rewritten pages no longer use.
UNUSED = ['assets', 'gilguard-logo-light.png', 'gilguard-logo-dark.png', 'build-timings.json']

# <img src="../gilguard-logo-light.png" ... class="navbar-logo light-content">
NAVBAR_LOGO = re.compile(r'<img src="[^"]*gilguard-logo-light\.png"([^>]*class="navbar-logo (light|dark)-content")')


def _rewrite(html: str) -> str:
    def repl(m: re.Match) -> str:
        url = LOGO_DARK if m.group(2) == 'dark' else LOGO_LIGHT
        return f'<img src="{url}"{m.group(1)}'

    # dark-mode-toggle.js resolves the dark logo next to the light one, so it lands on the CDN too.
    return NAVBAR_LOGO.sub(repl, html)


def main() -> int:
    subprocess.run(['uvx', 'great-docs', 'build'], cwd=ROOT, check=True)

    if SITE.exists():
        shutil.rmtree(SITE)
    shutil.copytree(BUILD, SITE)

    for name in UNUSED:
        p = SITE / name
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    pages = list(SITE.rglob('*.html'))
    for page in pages:
        page.write_text(_rewrite(page.read_text(encoding='utf-8')), encoding='utf-8')

    # Fail loudly if anything still points at a file we removed.
    stale = re.compile(r'(src|href)="(?!https?:)[^"]*(gilguard-logo-(light|dark)\.png|assets/)')
    leftovers = [str(p.relative_to(SITE)) for p in pages if stale.search(p.read_text(encoding='utf-8'))]
    if leftovers:
        print('Pages still reference removed local images:', *leftovers, sep='\n  ', file=sys.stderr)
        return 1

    print(f'Site ready in {SITE.relative_to(ROOT)}/ ({len(pages)} pages)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
