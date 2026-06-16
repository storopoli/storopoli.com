"""Post-process typst HTML output (stdin -> stdout).

1. Inject the constant <head> links (typst's default scaffold owns <head>;
   replacing it with a custom <html> element would break native footnotes).
2. Move the endnotes section, which typst appends at the very end of <body>,
   back inside <main> so it sits above the site footer.
3. Wrap block equations in a <div class="math-block"> scroll container so wide
   math scrolls instead of overflowing the column — the overflow must live on
   a wrapper, not the <math> element (see site.css for why).
4. Rewrite syntax-highlight colors (inline styles from typst's built-in
   default raw theme) into .tok-* classes so CSS can swap the palette per
   color scheme. Any color span left unmapped fails the build loudly: it
   means a typst upgrade changed the default theme's palette and this
   mapping needs updating.
"""

import re
import sys

# build.sh passes the fingerprinted stylesheet href (/css/site.<hash>.css)
CSS_HREF = sys.argv[1] if len(sys.argv) > 1 else "/css/site.css"

# Token colors of typst's built-in raw highlight theme (pinned: typst 0.15.0)
# mapped to palette-role classes defined in static/css/site.css
TOKEN_CLASSES = {
    "#74747c": "tok-gray",  # comments
    "#d73948": "tok-red",  # keywords, operators
    "#198810": "tok-green",  # strings
    "#301414": "tok-yellow",  # attributes (#[...] in rust)
    "#4b69c6": "tok-blue",  # function names
    "#8b41b1": "tok-purple",  # markup attribute names
    "#1d6c76": "tok-aqua",  # string escapes
    "#16718d": "tok-aqua",  # macros
    "#b60157": "tok-magenta",  # numbers, literals
}

HEAD = (
    '    <link rel="icon" type="image/svg+xml" href="/favicon.svg">\n'
    '    <meta name="theme-color" media="(prefers-color-scheme: light)" '
    'content="#fffcf0">\n'
    '    <meta name="theme-color" media="(prefers-color-scheme: dark)" '
    'content="#100f0f">\n'
    '    <link rel="preload" href="/fonts/newsreader-latin-opsz-normal.woff2" '
    'as="font" type="font/woff2" crossorigin>\n'
    '    <link rel="preload" href="/fonts/newsreader-latin-opsz-italic.woff2" '
    'as="font" type="font/woff2" crossorigin>\n'
    f'    <link rel="stylesheet" href="{CSS_HREF}">\n'
    '    <link rel="alternate" type="application/atom+xml" href="/atom.xml" '
    'title="Jose Storopoli, PhD - Atom Feed">\n'
)

ENDNOTES = re.compile(r"[ \t]*<section role=\"doc-endnotes\">.*?</section>\n?", re.S)

# Block equations only (display="block"); inline <math> is left alone. <math>
# never nests, so the first </math> closes the match.
BLOCK_MATH = re.compile(r'<math\b[^>]*\bdisplay="block"[^>]*>.*?</math>', re.S)

html = sys.stdin.read()

if "</head>" not in html:
    sys.exit("postprocess: no </head> found; typst scaffold changed?")
html = html.replace("</head>", HEAD + "  </head>", 1)

match = ENDNOTES.search(html)
if match:
    html = ENDNOTES.sub("", html, count=1)
    notes = match.group(0).rstrip("\n")
    html = html.replace("</main>", notes + "\n</main>", 1)

html = BLOCK_MATH.sub(
    lambda m: '<div class="math-block">' + m.group(0) + "</div>", html
)

for hex_color, cls in TOKEN_CLASSES.items():
    html = html.replace(f'<span style="color: {hex_color}">', f'<span class="{cls}">')

unmapped = sorted(set(re.findall(r'<span style="color: (#[0-9a-fA-F]{6})">', html)))
if unmapped:
    sys.exit(
        "postprocess: unmapped highlight colors (typst default theme changed?): "
        + ", ".join(unmapped)
    )

sys.stdout.write(html)
