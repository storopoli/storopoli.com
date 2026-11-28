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
5. Enhance <img> elements inside <main>: inject width/height/decoding="async"
   from the image manifest (preventing CLS), wrap images with a smaller WebP
   variant in <picture>, and prioritize the first content image for LCP
   (drop loading="lazy", add fetchpriority="high").
"""

from __future__ import annotations

import html as html_lib
import json
import re
import sys
from urllib.parse import quote

# build.sh passes the fingerprinted stylesheet href (/css/site.<hash>.css)
# and the image manifest path (.cache/image-manifest.json).
CSS_HREF = sys.argv[1] if len(sys.argv) > 1 else "/css/site.css"
IMAGE_MANIFEST_PATH = sys.argv[2] if len(sys.argv) > 2 else None

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

MAIN = re.compile(r"(<main\b[^>]*>)(.*?)(</main>)", re.S)
IMG_TAG = re.compile(r'<img\b(?:"[^"]*"|\'[^\']*\'|[^\'">])*?>', re.S)
ATTR = re.compile(
    r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)'
    r'(?:\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\'=<>`]+)))?'
)


def parse_img_attrs(tag: str) -> list[tuple[str, str | None]]:
    """Parse attributes from an <img ...> tag, preserving order."""
    inner = tag[4:-1].rstrip()
    if inner.endswith("/"):
        inner = inner[:-1]
    attrs: list[tuple[str, str | None]] = []
    for m in ATTR.finditer(inner):
        name = m.group(1).lower()
        raw_val = m.group(2) if m.group(2) is not None else (
            m.group(3) if m.group(3) is not None else m.group(4)
        )
        val = html_lib.unescape(raw_val) if raw_val is not None else None
        attrs.append((name, val))
    return attrs


def render_img_tag(attrs: list[tuple[str, str | None]]) -> str:
    parts = ["<img"]
    for name, val in attrs:
        if val is None:
            parts.append(f" {name}")
        else:
            parts.append(f' {name}="{html_lib.escape(val, quote=True)}"')
    parts.append(">")
    return "".join(parts)


def enhance_main_images(doc: str, manifest: dict[str, dict[str, object]]) -> str:
    """Rewrite <img> elements inside <main> for CLS, WebP <picture>, and LCP."""
    def rewrite_main(main_match: re.Match[str]) -> str:
        open_tag, body, close_tag = main_match.groups()
        img_index = 0

        def rewrite_img(img_match: re.Match[str]) -> str:
            nonlocal img_index
            is_first = img_index == 0
            img_index += 1

            attrs = parse_img_attrs(img_match.group(0))
            attr_map = {k: v for k, v in attrs}
            src = attr_map.get("src")
            entry = manifest.get(src) if src else None

            if is_first:
                attrs = [
                    (k, v)
                    for k, v in attrs
                    if not (k == "loading" and (v or "").lower() == "lazy")
                ]
                if "fetchpriority" not in attr_map:
                    attrs.append(("fetchpriority", "high"))

            if entry is not None:
                if "width" not in attr_map and "width" in entry:
                    attrs.append(("width", str(entry["width"])))
                if "height" not in attr_map and "height" in entry:
                    attrs.append(("height", str(entry["height"])))
                if "decoding" not in attr_map:
                    attrs.append(("decoding", "async"))

            rebuilt = render_img_tag(attrs)
            webp = entry.get("webp") if entry is not None else None
            if isinstance(webp, str) and webp:
                srcset = quote(webp, safe="/:@!$&'()*+,;=-._~")
                return (
                    f'<picture><source srcset="{html_lib.escape(srcset, quote=True)}" '
                    f'type="image/webp">{rebuilt}</picture>'
                )
            return rebuilt

        return open_tag + IMG_TAG.sub(rewrite_img, body) + close_tag

    return MAIN.sub(rewrite_main, doc, count=1)


image_manifest: dict[str, dict[str, object]] = {}
if IMAGE_MANIFEST_PATH:
    try:
        with open(IMAGE_MANIFEST_PATH, encoding="utf-8") as mf:
            image_manifest = json.load(mf)
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"postprocess: failed to read image manifest {IMAGE_MANIFEST_PATH}: {exc}")

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

html = enhance_main_images(html, image_manifest)

sys.stdout.write(html)
