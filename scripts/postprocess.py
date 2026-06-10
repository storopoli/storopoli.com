"""Post-process typst HTML output (stdin -> stdout).

1. Inject the constant <head> links (typst's default scaffold owns <head>;
   replacing it with a custom <html> element would break native footnotes).
2. Move the endnotes section, which typst appends at the very end of <body>,
   back inside <main> so it sits above the site footer.
3. Rewrite syntax-highlight colors (inline styles from the gruvbox-dark
   tmTheme) into .tok-* classes so CSS can swap the palette per color scheme.
"""

import re
import sys

# gruvbox-dark hex (as emitted by typst from themes/gruvbox-dark.tmTheme)
# mapped to palette-role classes defined in static/css/site.css
TOKEN_CLASSES = {
    "#928374": "tok-gray",
    "#fb4934": "tok-red",
    "#b8bb26": "tok-green",
    "#fabd2f": "tok-yellow",
    "#83a598": "tok-blue",
    "#d3869b": "tok-purple",
    "#8ec07c": "tok-aqua",
    "#fe8019": "tok-orange",
    "#ebdbb2": "tok-fg",
}

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

for hex_color, cls in TOKEN_CLASSES.items():
    html = html.replace(f'<span style="color: {hex_color}">', f'<span class="{cls}">')

sys.stdout.write(html)
