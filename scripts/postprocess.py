"""Post-process typst HTML output (stdin -> stdout).

1. Inject the constant <head> links (typst's default scaffold owns <head>;
   replacing it with a custom <html> element would break native footnotes).
2. Move the endnotes section, which typst appends at the very end of <body>,
   back inside <main> so it sits above the site footer.
"""

import re
import sys

HEAD = (
    '    <link rel="icon" type="image/svg+xml" href="/favicon.svg">\n'
    '    <link rel="stylesheet" href="/css/tufte.css">\n'
    '    <link rel="stylesheet" href="/css/site.css">\n'
    '    <link rel="alternate" type="application/atom+xml" href="/atom.xml" '
    'title="Jose Storopoli, PhD - Atom Feed">\n'
)

ENDNOTES = re.compile(r"[ \t]*<section role=\"doc-endnotes\">.*?</section>\n?", re.S)

html = sys.stdin.read()

if "</head>" not in html:
    sys.exit("postprocess: no </head> found; typst scaffold changed?")
html = html.replace("</head>", HEAD + "  </head>", 1)

match = ENDNOTES.search(html)
if match:
    html = ENDNOTES.sub("", html, count=1)
    notes = match.group(0).rstrip("\n")
    html = html.replace("</main>", notes + "\n</main>", 1)

sys.stdout.write(html)
