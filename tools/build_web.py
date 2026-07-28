# Wrap patchkaart.html (an Artifact fragment: <title> + <style> + body)
# into a standalone page for synthesizer.sierk.dev.
#
#   python tools/build_web.py            -> writes build/index.html
#
# Deploy:
#   scp -i ~/.ssh/openclaw_key build/index.html \
#       root@187.124.0.172:/srv/apps/synthesizer/public/index.html
#   ssh ... "chown synthesizer:synthesizer /srv/apps/synthesizer/public/index.html"

import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'patchkaart.html')
OUT_DIR = os.path.join(HERE, 'build')
OUT = os.path.join(OUT_DIR, 'index.html')

HEAD_EXTRA = """<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Patchkaart voor de Weermachine WM-1 — tempo-locked soundscape-instrument op AMYboard.">
<meta name="theme-color" content="#EFECE3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0C1014" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="WM-1">"""


def main():
    with open(SRC, encoding='utf-8') as f:
        text = f.read()

    title = re.search(r'<title>.*?</title>', text, re.S)
    style = re.search(r'<style>.*?</style>', text, re.S)
    if not title or not style:
        raise SystemExit('patchkaart.html misses <title> or <style>')
    body = text[style.end():].strip()

    page = '\n'.join([
        '<!doctype html>',
        '<html lang="nl">',
        '<head>',
        '<meta charset="utf-8">',
        title.group(0),
        HEAD_EXTRA,
        style.group(0),
        '</head>',
        '<body>',
        '',
        body,
        '',
        '</body>',
        '</html>',
        '',
    ])

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)
    version = re.search(r'SKETCH v[0-9.]+', page)
    print('wrote %s (%d bytes, %s)'
          % (OUT, len(page.encode('utf-8')),
             version.group(0) if version else 'no version tag'))


if __name__ == '__main__':
    main()
