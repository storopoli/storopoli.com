#!/usr/bin/env python3
"""Build storopoli.com: Markdown -> Typst -> HTML, Atom feed, and sitemap.

Stdlib-only build orchestrator replacing build.sh's jq/xargs/typst-eval
pipeline, postprocess.py, and gen-feed.py:

1. Incrementally converts Markdown bodies (posts + pages) to Typst markup via
   Pandoc + scripts/body-filter.lua, caching outputs in .cache/bodies/ keyed on
   the input file, Lua filter, and Pandoc version.
2. Parses YAML frontmatter directly in Python (zero `typst eval` / `jq`
   spawns), computes reading time, and writes .cache/posts.json.
3. Compiles posts, standalone pages, and listings in parallel via Typst 0.15.0
   HTML export, failing loudly on any unexpected Typst warning.
4. Post-processes every HTML page in-process with html.parser:
   - injects per-page <head> links, canonical, OpenGraph, and Twitter tags;
   - relocates Typst's <section role="doc-endnotes"> inside <article>/<main>;
   - wraps block <math display="block"> equations in <div class="math-block">;
   - wraps <table> elements inside <main> in <div class="table-wrap">;
   - wraps language-tagged <pre><code data-lang="..."> blocks in
     <div class="code-block"><div class="code-lang">...</div><pre>...</pre></div>;
   - rewrites Typst syntax-highlight hex colors into .tok-* classes (failing
     loudly on any unmapped color);
   - injects clickable `#` anchor links on h2–h4 headings with an `id`.
5. Checks all built HTML for silently escaped raw HTML outside <code>/<pre>.
6. Generates and validates atom.xml (full content with inlined light-mode
   Flexoki code colors, categories, updated timestamps, and /atom.xsl) and
   sitemap.xml.
7. Builds into a temporary staging directory and swaps it into _site/ so
   `just serve` never serves 404s during `just watch`.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import datetime
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import quote
import xml.etree.ElementTree as ET

SITE_URL = "https://storopoli.com"
SITE_TITLE = "Jose Storopoli, PhD"
AUTHOR_NAME = "Jose Storopoli, PhD"
AUTHOR_DEFAULT = "Jose Storopoli"
AUTHOR_EMAIL = "jose@storopoli.com"

INDEX_DESCRIPTION = (
    "Personal website and blog of Jose Storopoli, PhD — cryptography, "
    "mathematics, security engineering, Rust, and distributed systems."
)
ARCHIVE_DESCRIPTION = (
    "Complete archive of all posts by Jose Storopoli, PhD, "
    "organized chronologically and by tag."
)
TAG_DESCRIPTION_TEMPLATE = 'All posts tagged "{tag}" on Jose Storopoli\'s blog.'

# Token colors of Typst's built-in default raw highlight theme (pinned: 0.15.0)
# mapped to Flexoki role classes defined in static/css/site.css.
TOKEN_CLASSES: dict[str, str] = {
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

# Light-mode WCAG AA Flexoki hex colors (mirrored from static/css/site.css)
# for inlining into the Atom feed where external CSS is unavailable.
FEED_TOKEN_COLORS: dict[str, str] = {
    "tok-gray": "#575653",
    "tok-red": "#af3029",
    "tok-green": "#536907",
    "tok-yellow": "#664d01",
    "tok-blue": "#205ea6",
    "tok-purple": "#5e409d",
    "tok-aqua": "#1c6c66",
    "tok-magenta": "#a02f6f",
}

HTML_VOID_ELEMENTS: frozenset[str] = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)

WORDS_PER_MINUTE = 200


class BuildError(RuntimeError):
    """Raised when any build, compilation, or validation step fails."""


@dataclass(frozen=True)
class PageMeta:
    """Per-page SEO and post-processing metadata."""

    title: str
    description: str
    canonical_url: str
    og_type: str = "website"
    published_time: str | None = None
    modified_time: str | None = None
    noindex: bool = False
    add_heading_anchors: bool = True


# ---------------------------------------------------------------------------
# Slugification
# ---------------------------------------------------------------------------


def slugify(text: str) -> str:
    """Convert text into an ASCII lowercase hyphenated slug.

    Must stay aligned with `slugify` in `lib/template.typ`:
    `lower(s).replace(regex("[^a-z0-9]+"), "-").trim("-")`.
    """
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ---------------------------------------------------------------------------
# Stdlib-only YAML frontmatter parser
# ---------------------------------------------------------------------------

_DOUBLE_ESCAPES: dict[str, str] = {
    "\\": "\\",
    '"': '"',
    "/": "/",
    "0": "\0",
    "a": "\a",
    "b": "\b",
    "t": "\t",
    "n": "\n",
    "v": "\v",
    "f": "\f",
    "r": "\r",
    "e": "\x1b",
    " ": " ",
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INT_RE = re.compile(r"^[+-]?\d+$")
_KEY_VAL_RE = re.compile(r"^([A-Za-z0-9_-]+)\s*:(?:[ \t]+(.*)|[ \t]*)$")
_BLOCK_ITEM_RE = re.compile(r"^[ \t]*-[ \t]*(.*)$")


def split_frontmatter(text: str, source: str = "<string>") -> tuple[str, str]:
    """Split a Markdown document into `(frontmatter_yaml, body_markdown)`.

    Handles UTF-8 BOM, CRLF/CR line endings, and extra `---` thematic breaks
    later in the document body.
    """
    if text.startswith("\ufeff"):
        text = text[1:]
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = norm.split("\n")
    if not lines or lines[0].rstrip(" \t") != "---":
        raise ValueError(f"{source}: missing opening '---' YAML frontmatter delimiter")

    for idx in range(1, len(lines)):
        stripped = lines[idx].rstrip(" \t")
        if stripped in ("---", "..."):
            fm_text = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1 :])
            return fm_text, body

    raise ValueError(f"{source}: unclosed YAML frontmatter (missing closing '---')")


def _strip_inline_comment(raw: str) -> str:
    """Strip a YAML `# ...` comment outside quotes."""
    in_single = False
    in_double = False
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if in_double:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == '"':
                in_double = False
        elif in_single:
            if ch == "'":
                if i + 1 < n and raw[i + 1] == "'":
                    i += 2
                    continue
                in_single = False
        else:
            if ch == '"':
                in_double = True
            elif ch == "'":
                in_single = True
            elif ch == "#" and (i == 0 or raw[i - 1] in (" ", "\t")):
                return raw[:i].rstrip(" \t")
        i += 1
    return raw.rstrip(" \t")


def _unescape_double_quoted(raw: str, source: str, lineno: int) -> str:
    """Decode a YAML double-quoted string (including the surrounding quotes)."""
    if len(raw) < 2 or not raw.startswith('"') or not raw.endswith('"'):
        raise ValueError(f"{source}:{lineno}: unterminated double-quoted string")
    inner = raw[1:-1]
    out: list[str] = []
    i = 0
    n = len(inner)
    while i < n:
        ch = inner[i]
        if ch == "\\":
            if i + 1 >= n:
                raise ValueError(f"{source}:{lineno}: trailing backslash in double-quoted string")
            esc = inner[i + 1]
            if esc in _DOUBLE_ESCAPES:
                out.append(_DOUBLE_ESCAPES[esc])
                i += 2
            elif esc == "x" and i + 3 < n:
                out.append(chr(int(inner[i + 2 : i + 4], 16)))
                i += 4
            elif esc == "u" and i + 5 < n:
                out.append(chr(int(inner[i + 2 : i + 6], 16)))
                i += 6
            elif esc == "U" and i + 9 < n:
                out.append(chr(int(inner[i + 2 : i + 10], 16)))
                i += 10
            else:
                raise ValueError(f"{source}:{lineno}: unsupported escape '\\{esc}'")
        elif ch == '"':
            raise ValueError(f"{source}:{lineno}: unescaped quote inside double-quoted string")
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _unescape_single_quoted(raw: str, source: str, lineno: int) -> str:
    """Decode a YAML single-quoted string (with `''` -> `'`)."""
    if len(raw) < 2 or not raw.startswith("'") or not raw.endswith("'"):
        raise ValueError(f"{source}:{lineno}: unterminated single-quoted string")
    inner = raw[1:-1]
    out: list[str] = []
    i = 0
    n = len(inner)
    while i < n:
        if inner[i] == "'":
            if i + 1 < n and inner[i + 1] == "'":
                out.append("'")
                i += 2
            else:
                raise ValueError(f"{source}:{lineno}: unescaped quote inside single-quoted string")
        else:
            out.append(inner[i])
            i += 1
    return "".join(out)


def _split_flow_list(inner: str, source: str, lineno: int) -> list[str]:
    """Split items inside `[...]` on commas outside quotes."""
    items: list[str] = []
    buf: list[str] = []
    in_single = False
    in_double = False
    i = 0
    n = len(inner)
    while i < n:
        ch = inner[i]
        if in_double:
            buf.append(ch)
            if ch == "\\" and i + 1 < n:
                buf.append(inner[i + 1])
                i += 2
                continue
            if ch == '"':
                in_double = False
        elif in_single:
            buf.append(ch)
            if ch == "'":
                if i + 1 < n and inner[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                in_single = False
        else:
            if ch == '"':
                in_double = True
                buf.append(ch)
            elif ch == "'":
                in_single = True
                buf.append(ch)
            elif ch == ",":
                items.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
        i += 1
    if in_single or in_double:
        raise ValueError(f"{source}:{lineno}: unterminated quote inside inline list")
    tail = "".join(buf).strip()
    if tail or items:
        if tail:
            items.append(tail)
    return items


def parse_yaml_value(raw: str, source: str = "<string>", lineno: int = 1) -> Any:
    """Parse a YAML scalar or inline `[a, b]` list."""
    val = _strip_inline_comment(raw).strip()
    if not val:
        return None
    if val.startswith('"'):
        return _unescape_double_quoted(val, source, lineno)
    if val.startswith("'"):
        return _unescape_single_quoted(val, source, lineno)
    if val.startswith("["):
        if not val.endswith("]"):
            raise ValueError(f"{source}:{lineno}: unterminated inline list")
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [
            parse_yaml_value(part, source, lineno)
            for part in _split_flow_list(inner, source, lineno)
        ]

    lower = val.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("null", "~"):
        return None
    if _INT_RE.fullmatch(val):
        return int(val)
    if _DATE_RE.fullmatch(val):
        try:
            datetime.date.fromisoformat(val)
        except ValueError as exc:
            raise ValueError(f"{source}:{lineno}: invalid ISO date {val!r}") from exc
        return val
    return val


def parse_frontmatter(text: str, source: str = "<string>") -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and return `(metadata, body_markdown)`."""
    fm_text, body = split_frontmatter(text, source)
    data: dict[str, Any] = {}
    lines = fm_text.split("\n")
    i = 0
    current_block_key: str | None = None

    while i < len(lines):
        line = lines[i]
        lineno = i + 2  # line 1 is opening '---'
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Block sequence item (`- value` or `  - value`) under a preceding key.
        if current_block_key is not None:
            item_match = _BLOCK_ITEM_RE.match(line)
            if item_match and (line.startswith((" ", "\t")) or line.lstrip().startswith("-")):
                if data[current_block_key] is None:
                    data[current_block_key] = []
                if not isinstance(data[current_block_key], list):
                    raise ValueError(
                        f"{source}:{lineno}: unexpected list item under {current_block_key!r}"
                    )
                data[current_block_key].append(
                    parse_yaml_value(item_match.group(1), source, lineno)
                )
                i += 1
                continue
            if not line.startswith((" ", "\t")):
                current_block_key = None

        kv = _KEY_VAL_RE.match(line)
        if not kv:
            raise ValueError(f"{source}:{lineno}: malformed frontmatter line: {line!r}")

        key = kv.group(1)
        raw_val = kv.group(2) if kv.group(2) is not None else ""
        cleaned_val = _strip_inline_comment(raw_val).strip()

        if cleaned_val in ("|", "|-", ">", ">-"):
            fold = cleaned_val.startswith(">")
            chomp_strip = cleaned_val.endswith("-")
            block_lines: list[str] = []
            block_indent: int | None = None
            i += 1
            while i < len(lines):
                bline = lines[i]
                if not bline.strip():
                    block_lines.append("")
                    i += 1
                    continue
                indent = len(bline) - len(bline.lstrip(" "))
                if indent == 0:
                    break
                if block_indent is None:
                    block_indent = indent
                block_lines.append(bline[min(indent, block_indent) :])
                i += 1
            if fold:
                joined = " ".join(part.strip() for part in block_lines if part.strip())
            else:
                joined = "\n".join(block_lines)
            data[key] = joined.rstrip("\n") if chomp_strip else joined
            current_block_key = None
            continue

        if cleaned_val == "":
            data[key] = None
            current_block_key = key
        else:
            data[key] = parse_yaml_value(raw_val, source, lineno)
            current_block_key = None
        i += 1

    return data, body


# ---------------------------------------------------------------------------
# Reading time estimation
# ---------------------------------------------------------------------------


def estimate_reading_time(markdown_body: str, wpm: int = WORDS_PER_MINUTE) -> int:
    """Estimate reading time in whole minutes (minimum 1) from Markdown body."""
    text = markdown_body
    # Replace images and links with their visible text so long URLs don't skew counts.
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    # Strip bare URLs, HTML tags, and footnote markers/definitions.
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\[\^[^\]]+\]:?", " ", text)
    words = re.findall(r"[A-Za-z0-9]+(?:['’\-][A-Za-z0-9]+)*", text)
    return max(1, round(len(words) / wpm))


# ---------------------------------------------------------------------------
# HTML parsing & rewriting (html.parser, zero regex HTML surgery)
# ---------------------------------------------------------------------------


def format_start_tag(
    tag: str,
    attrs: list[tuple[str, str | None]],
    self_closing: bool = False,
) -> str:
    """Serialize an HTML start (or self-closing) tag with escaped attributes."""
    parts = [f"<{tag}"]
    for name, value in attrs:
        if value is None:
            parts.append(f" {name}")
        else:
            parts.append(f' {name}="{html.escape(value, quote=True)}"')
    parts.append("/>" if self_closing else ">")
    return "".join(parts)


def _rewrite_token_span_attrs(
    attrs: list[tuple[str, str | None]],
    unmapped_colors: set[str],
) -> tuple[bool, list[tuple[str, str | None]]]:
    """Rewrite Typst syntax-highlight `style="color: #xxxxxx"` to `.tok-*`."""
    style_idx: int | None = None
    class_idx: int | None = None
    for idx, (name, _) in enumerate(attrs):
        low = name.lower()
        if low == "style":
            style_idx = idx
        elif low == "class":
            class_idx = idx

    if style_idx is None:
        return False, attrs

    style_val = attrs[style_idx][1] or ""
    decls = [d.strip() for d in style_val.split(";") if d.strip()]
    added_classes: list[str] = []
    remaining_decls: list[str] = []
    changed = False

    for decl in decls:
        m = re.fullmatch(r"color\s*:\s*(#[0-9a-fA-F]{6})", decl, flags=re.IGNORECASE)
        if m:
            hex_color = m.group(1).lower()
            tok_cls = TOKEN_CLASSES.get(hex_color)
            if tok_cls is not None:
                added_classes.append(tok_cls)
                changed = True
            else:
                unmapped_colors.add(hex_color)
                remaining_decls.append(decl)
        else:
            remaining_decls.append(decl)

    if not changed:
        return False, attrs

    new_attrs: list[tuple[str, str | None]] = []
    if class_idx is None:
        for idx, (name, value) in enumerate(attrs):
            if idx == style_idx:
                new_attrs.append(("class", " ".join(added_classes)))
                if remaining_decls:
                    new_attrs.append(("style", "; ".join(remaining_decls)))
            else:
                new_attrs.append((name, value))
    else:
        for idx, (name, value) in enumerate(attrs):
            if idx == style_idx:
                if remaining_decls:
                    new_attrs.append(("style", "; ".join(remaining_decls)))
            elif idx == class_idx:
                existing = (value or "").split()
                for cls in added_classes:
                    if cls not in existing:
                        existing.append(cls)
                new_attrs.append((name, " ".join(existing)))
            else:
                new_attrs.append((name, value))
    return True, new_attrs


class _PagePostprocessor(HTMLParser):
    """Streaming HTMLParser pass that transforms Typst HTML output."""

    def __init__(
        self,
        css_href: str,
        meta: PageMeta,
        image_manifest: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(convert_charrefs=False)
        self.css_href = css_href
        self.meta = meta
        self.image_manifest = image_manifest or {}
        self.out: list[str] = []
        self.endnotes: list[str] = []
        self.capturing_endnotes_depth = 0
        self.in_head = False
        self.seen_head_close = False
        self.has_description_meta = False
        self.in_main = False
        self.main_depth = 0
        self.main_img_count = 0
        self.article_depth = 0
        self.article_close_idx: int | None = None
        self.main_close_idx: int | None = None
        self.math_block_stack: list[bool] = []
        self.table_depth = 0
        self.pending_pre_chunks: list[str] | None = None
        self.pre_code_block_stack: list[bool] = []
        self.heading_anchor_stack: list[str | None] = []
        self.unmapped_colors: set[str] = set()

    def _flush_pending_pre(self, lang: str | None = None) -> None:
        chunks = self.pending_pre_chunks
        if chunks is None:
            return
        self.pending_pre_chunks = None
        if lang:
            escaped_lang = html.escape(lang, quote=False)
            self._emit(f'<div class="code-block"><div class="code-lang">{escaped_lang}</div>')
            for chunk in chunks:
                self._emit(chunk)
            self.pre_code_block_stack.append(True)
        else:
            for chunk in chunks:
                self._emit(chunk)
            self.pre_code_block_stack.append(False)

    def _enhance_img(self, attrs: list[tuple[str, str | None]]) -> str:
        """Enhance an <img> inside <main> for CLS, WebP <picture>, and LCP."""
        is_first = self.main_img_count == 0
        self.main_img_count += 1

        new_attrs = list(attrs)
        attr_map = {k.lower(): v for k, v in new_attrs}
        src = attr_map.get("src")
        entry = self.image_manifest.get(src) if src else None

        if is_first:
            new_attrs = [
                (k, v)
                for k, v in new_attrs
                if not (k.lower() == "loading" and (v or "").lower() == "lazy")
            ]
            if "fetchpriority" not in attr_map:
                new_attrs.append(("fetchpriority", "high"))

        if entry is not None:
            if "width" not in attr_map and "width" in entry:
                new_attrs.append(("width", str(entry["width"])))
            if "height" not in attr_map and "height" in entry:
                new_attrs.append(("height", str(entry["height"])))
            if "decoding" not in attr_map:
                new_attrs.append(("decoding", "async"))

        rebuilt = format_start_tag("img", new_attrs)
        webp = entry.get("webp") if entry is not None else None
        if isinstance(webp, str) and webp:
            srcset = quote(webp, safe="/:@!$&'()*+,;=-._~")
            return (
                f'<picture><source srcset="{html.escape(srcset, quote=True)}" '
                f'type="image/webp">{rebuilt}</picture>'
            )
        return rebuilt

    def _emit(self, chunk: str) -> None:
        if self.capturing_endnotes_depth > 0:
            self.endnotes.append(chunk)
        else:
            self.out.append(chunk)

    def _render_head_tags(self) -> str:
        esc = lambda s: html.escape(s, quote=True)  # noqa: E731
        lines = [
            '    <link rel="icon" type="image/svg+xml" href="/favicon.svg">',
            '    <meta name="theme-color" media="(prefers-color-scheme: light)" content="#fffcf0">',
            '    <meta name="theme-color" media="(prefers-color-scheme: dark)" content="#100f0f">',
            '    <link rel="preload" href="/fonts/newsreader-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>',
            '    <link rel="preload" href="/fonts/newsreader-latin-opsz-italic.woff2" as="font" type="font/woff2" crossorigin>',
            f'    <link rel="stylesheet" href="{esc(self.css_href)}">',
            f'    <link rel="alternate" type="application/atom+xml" href="/atom.xml" title="{esc(SITE_TITLE)} - Atom Feed">',
        ]
        if self.meta.description and not self.has_description_meta:
            lines.append(f'    <meta name="description" content="{esc(self.meta.description)}">')
        if self.meta.noindex:
            lines.append('    <meta name="robots" content="noindex">')
        lines.extend(
            [
                f'    <link rel="canonical" href="{esc(self.meta.canonical_url)}">',
                f'    <meta property="og:site_name" content="{esc(SITE_TITLE)}">',
                f'    <meta property="og:title" content="{esc(self.meta.title)}">',
                f'    <meta property="og:description" content="{esc(self.meta.description)}">',
                f'    <meta property="og:url" content="{esc(self.meta.canonical_url)}">',
                f'    <meta property="og:type" content="{esc(self.meta.og_type)}">',
            ]
        )
        if self.meta.og_type == "article" and self.meta.published_time:
            lines.append(
                f'    <meta property="article:published_time" content="{esc(self.meta.published_time)}">'
            )
            if self.meta.modified_time and self.meta.modified_time != self.meta.published_time:
                lines.append(
                    f'    <meta property="article:modified_time" content="{esc(self.meta.modified_time)}">'
                )
        lines.extend(
            [
                '    <meta name="twitter:card" content="summary">',
                f'    <meta name="twitter:title" content="{esc(self.meta.title)}">',
                f'    <meta name="twitter:description" content="{esc(self.meta.description)}">',
            ]
        )
        return "\n".join(lines) + "\n  "

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_l = tag.lower()
        attr_dict = {k.lower(): v for k, v in attrs}

        if self.pending_pre_chunks is not None:
            if tag_l == "code":
                lang = (attr_dict.get("data-lang") or "").strip()
                self._flush_pending_pre(lang or None)
            else:
                self._flush_pending_pre(None)

        if tag_l == "head":
            self.in_head = True
            self._emit(self.get_starttag_text() or format_start_tag(tag, attrs))
            return

        if (
            self.in_head
            and tag_l == "meta"
            and (attr_dict.get("name") or "").lower() == "description"
        ):
            self.has_description_meta = True

        if tag_l == "main":
            self.in_main = True
            self.main_depth += 1
        elif tag_l == "article" and self.in_main and self.capturing_endnotes_depth == 0:
            self.article_depth += 1

        if tag_l == "section":
            if self.capturing_endnotes_depth > 0:
                self.capturing_endnotes_depth += 1
            elif attr_dict.get("role") == "doc-endnotes":
                self.capturing_endnotes_depth = 1

        if tag_l == "math":
            is_block = attr_dict.get("display") == "block"
            self.math_block_stack.append(is_block)
            if is_block:
                self._emit('<div class="math-block">')

        if tag_l == "table" and (self.in_main or self.capturing_endnotes_depth > 0):
            if self.table_depth == 0:
                self._emit('<div class="table-wrap">')
            self.table_depth += 1

        if tag_l == "span":
            changed, new_attrs = _rewrite_token_span_attrs(attrs, self.unmapped_colors)
            if changed:
                self._emit(format_start_tag(tag, new_attrs))
                return

        if tag_l == "img" and self.in_main and self.capturing_endnotes_depth == 0:
            self._emit(self._enhance_img(attrs))
            return

        if (
            self.meta.add_heading_anchors
            and self.in_main
            and self.capturing_endnotes_depth == 0
            and tag_l in ("h2", "h3", "h4")
        ):
            heading_id = attr_dict.get("id")
            self.heading_anchor_stack.append(heading_id if heading_id else None)

        if tag_l == "pre" and (self.in_main or self.capturing_endnotes_depth > 0):
            self.pending_pre_chunks = [self.get_starttag_text() or format_start_tag(tag, attrs)]
            return

        self._emit(self.get_starttag_text() or format_start_tag(tag, attrs))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_l = tag.lower()
        attr_dict = {k.lower(): v for k, v in attrs}

        if self.pending_pre_chunks is not None:
            if tag_l == "code":
                lang = (attr_dict.get("data-lang") or "").strip()
                self._flush_pending_pre(lang or None)
            else:
                self._flush_pending_pre(None)

        if (
            self.in_head
            and tag_l == "meta"
            and (attr_dict.get("name") or "").lower() == "description"
        ):
            self.has_description_meta = True

        raw = self.get_starttag_text() or format_start_tag(tag, attrs, self_closing=True)
        if tag_l == "math" and attr_dict.get("display") == "block":
            self._emit(f'<div class="math-block">{raw}</div>')
            return
        if tag_l == "span":
            changed, new_attrs = _rewrite_token_span_attrs(attrs, self.unmapped_colors)
            if changed:
                self._emit(format_start_tag(tag, new_attrs, self_closing=True))
                return
        if tag_l == "img" and self.in_main and self.capturing_endnotes_depth == 0:
            self._emit(self._enhance_img(attrs))
            return
        self._emit(raw)

    def handle_endtag(self, tag: str) -> None:
        tag_l = tag.lower()

        if self.pending_pre_chunks is not None:
            self._flush_pending_pre(None)

        if tag_l == "head":
            self.in_head = False
            self.seen_head_close = True
            self._emit(self._render_head_tags())
            self._emit(f"</{tag}>")
            return

        if (
            self.meta.add_heading_anchors
            and self.in_main
            and self.capturing_endnotes_depth == 0
            and tag_l in ("h2", "h3", "h4")
            and self.heading_anchor_stack
        ):
            heading_id = self.heading_anchor_stack.pop()
            if heading_id:
                escaped_id = html.escape(heading_id, quote=True)
                self._emit(
                    f'<a class="heading-anchor" href="#{escaped_id}" '
                    'aria-label="Link to this section">#</a>'
                )

        if tag_l == "article" and self.in_main and self.capturing_endnotes_depth == 0:
            if self.article_depth == 1:
                self.article_close_idx = len(self.out)
            if self.article_depth > 0:
                self.article_depth -= 1
        elif tag_l == "main" and self.capturing_endnotes_depth == 0:
            if self.main_depth == 1:
                self.main_close_idx = len(self.out)
                self.in_main = False
            if self.main_depth > 0:
                self.main_depth -= 1

        self._emit(f"</{tag}>")

        if tag_l == "pre" and self.pre_code_block_stack:
            if self.pre_code_block_stack.pop():
                self._emit("</div>")

        if tag_l == "table" and (self.in_main or self.capturing_endnotes_depth > 0) and self.table_depth > 0:
            self.table_depth -= 1
            if self.table_depth == 0:
                self._emit("</div>")

        if tag_l == "math" and self.math_block_stack:
            if self.math_block_stack.pop():
                self._emit("</div>")

        if tag_l == "section" and self.capturing_endnotes_depth > 0:
            self.capturing_endnotes_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.pending_pre_chunks is not None:
            if data.strip() == "":
                self.pending_pre_chunks.append(data)
                return
            self._flush_pending_pre(None)
        self._emit(data)

    def handle_entityref(self, name: str) -> None:
        if self.pending_pre_chunks is not None:
            self._flush_pending_pre(None)
        self._emit(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self.pending_pre_chunks is not None:
            self._flush_pending_pre(None)
        self._emit(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        if self.pending_pre_chunks is not None:
            self._flush_pending_pre(None)
        self._emit(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        if self.pending_pre_chunks is not None:
            self._flush_pending_pre(None)
        self._emit(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        if self.pending_pre_chunks is not None:
            self._flush_pending_pre(None)
        self._emit(f"<?{data}>")

    def finalize(self) -> str:
        if self.pending_pre_chunks is not None:
            self._flush_pending_pre(None)
        if not self.seen_head_close:
            raise BuildError("postprocess: no </head> found; typst scaffold changed?")
        if self.unmapped_colors:
            raise BuildError(
                "postprocess: unmapped highlight colors (typst default theme changed?): "
                + ", ".join(sorted(self.unmapped_colors))
            )
        if self.endnotes:
            insert_idx = (
                self.article_close_idx
                if self.article_close_idx is not None
                else self.main_close_idx
            )
            if insert_idx is None:
                raise BuildError("postprocess: found doc-endnotes but no </main>")
            notes_html = "".join(self.endnotes).strip()
            self.out.insert(insert_idx, "\n" + notes_html + "\n")
        return "".join(self.out)


def postprocess_html(
    raw_html: str,
    css_href: str,
    meta: PageMeta,
    image_manifest: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Post-process one Typst HTML document using html.parser."""
    parser = _PagePostprocessor(
        css_href=css_href, meta=meta, image_manifest=image_manifest
    )
    parser.feed(raw_html)
    parser.close()
    return parser.finalize()


class _FeedContentExtractor(HTMLParser):
    """Extract clean article HTML for atom.xml using html.parser.

    - Keeps only the inner HTML of `<main>`.
    - Strips chrome: first `<h1>`, `.post-meta`, `#table-of-contents`,
      `.post-nav`, `.heading-anchor` links, and `.code-lang` bars.
    - Unwraps `<picture>` wrappers back to their fallback `<img>` (stripping
      `<source>`), and unwraps `.code-block` and `.table-wrap` layout divs so
      feed readers receive clean `<pre><code>` and `<table>` elements.
    - Absolutizes root-relative `href="/..."` and `src="/..."` ONLY on real
      HTML element attributes (never inside `<code>`/`<pre>` text).
    - Inlines light-mode Flexoki hex colors on `.tok-*` spans so syntax
      highlighting renders in feed readers without external CSS.
    """

    def __init__(self, site_url: str = SITE_URL) -> None:
        super().__init__(convert_charrefs=False)
        self.site_url = site_url.rstrip("/")
        self.out: list[str] = []
        self.found_main = False
        self.in_main = False
        self.main_depth = 0
        self.picture_depth = 0
        self.div_unwrap_stack: list[bool] = []
        self.stripped_h1 = False
        self.skip_stack: list[str] = []

    def _should_skip(self, tag_l: str, attr_dict: dict[str, str | None]) -> bool:
        classes = set((attr_dict.get("class") or "").split())
        if tag_l == "h1" and not self.stripped_h1:
            self.stripped_h1 = True
            return True
        if tag_l == "div" and ("post-meta" in classes or "code-lang" in classes):
            return True
        if tag_l == "details" and attr_dict.get("id") == "table-of-contents":
            return True
        if tag_l == "nav" and "post-nav" in classes:
            return True
        if tag_l == "a" and "heading-anchor" in classes:
            return True
        return False

    def _transform_attrs(
        self, tag_l: str, attrs: list[tuple[str, str | None]]
    ) -> tuple[bool, list[tuple[str, str | None]]]:
        changed = False
        new_attrs: list[tuple[str, str | None]] = []
        inline_color: str | None = None

        for name, value in attrs:
            low = name.lower()
            if low in ("href", "src") and value is not None:
                if value.startswith("/") and not value.startswith("//"):
                    new_attrs.append((name, f"{self.site_url}{value}"))
                    changed = True
                    continue
            if tag_l == "span" and low == "class" and value is not None:
                tokens = value.split()
                kept: list[str] = []
                for tok in tokens:
                    if tok in FEED_TOKEN_COLORS and inline_color is None:
                        inline_color = FEED_TOKEN_COLORS[tok]
                        changed = True
                    else:
                        kept.append(tok)
                if kept:
                    new_attrs.append((name, " ".join(kept)))
                continue
            new_attrs.append((name, value))

        if inline_color is not None:
            merged = False
            for idx, (name, value) in enumerate(new_attrs):
                if name.lower() == "style":
                    existing = (value or "").strip().rstrip(";")
                    combined = f"color: {inline_color}; {existing}" if existing else f"color: {inline_color}"
                    new_attrs[idx] = (name, combined)
                    merged = True
                    break
            if not merged:
                new_attrs.append(("style", f"color: {inline_color}"))

        return changed, new_attrs

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_l = tag.lower()
        if not self.in_main:
            if tag_l == "main" and not self.found_main:
                self.found_main = True
                self.in_main = True
                self.main_depth = 1
            return

        if tag_l == "main":
            self.main_depth += 1

        if self.skip_stack:
            if tag_l not in HTML_VOID_ELEMENTS:
                self.skip_stack.append(tag_l)
            return

        if tag_l == "picture":
            self.picture_depth += 1
            return
        if tag_l == "source" and self.picture_depth > 0:
            return

        attr_dict = {k.lower(): v for k, v in attrs}
        if self._should_skip(tag_l, attr_dict):
            if tag_l not in HTML_VOID_ELEMENTS:
                self.skip_stack.append(tag_l)
            return

        if tag_l == "div":
            classes = set((attr_dict.get("class") or "").split())
            if "code-block" in classes or "table-wrap" in classes:
                self.div_unwrap_stack.append(True)
                return
            self.div_unwrap_stack.append(False)

        changed, new_attrs = self._transform_attrs(tag_l, attrs)
        if changed:
            self.out.append(format_start_tag(tag, new_attrs))
        else:
            self.out.append(self.get_starttag_text() or format_start_tag(tag, attrs))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self.in_main or self.skip_stack:
            return
        tag_l = tag.lower()
        if tag_l == "source" and self.picture_depth > 0:
            return
        attr_dict = {k.lower(): v for k, v in attrs}
        if self._should_skip(tag_l, attr_dict):
            return
        changed, new_attrs = self._transform_attrs(tag_l, attrs)
        if changed:
            self.out.append(format_start_tag(tag, new_attrs, self_closing=True))
        else:
            self.out.append(
                self.get_starttag_text() or format_start_tag(tag, attrs, self_closing=True)
            )

    def handle_endtag(self, tag: str) -> None:
        if not self.in_main:
            return
        tag_l = tag.lower()
        if tag_l == "main":
            self.main_depth -= 1
            if self.main_depth == 0:
                self.in_main = False
                return
        if self.skip_stack:
            if self.skip_stack[-1] == tag_l:
                self.skip_stack.pop()
            elif tag_l in self.skip_stack:
                while self.skip_stack and self.skip_stack[-1] != tag_l:
                    self.skip_stack.pop()
                if self.skip_stack:
                    self.skip_stack.pop()
            return
        if tag_l == "picture" and self.picture_depth > 0:
            self.picture_depth -= 1
            return
        if tag_l == "div" and self.div_unwrap_stack:
            if self.div_unwrap_stack.pop():
                return
        self.out.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self.in_main and not self.skip_stack:
            self.out.append(data)

    def handle_entityref(self, name: str) -> None:
        if self.in_main and not self.skip_stack:
            self.out.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self.in_main and not self.skip_stack:
            self.out.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        if self.in_main and not self.skip_stack:
            self.out.append(f"<!--{data}-->")


def extract_feed_content(page_html: str, site_url: str = SITE_URL) -> str | None:
    """Return feed-safe inner HTML for a post page, or None if no `<main>`."""
    parser = _FeedContentExtractor(site_url=site_url)
    parser.feed(page_html)
    parser.close()
    if not parser.found_main:
        return None
    content = "".join(parser.out).strip()
    return content or None


class _EscapedHtmlChecker(HTMLParser):
    """Detect silently escaped raw HTML tags outside `<code>` / `<pre>`."""

    _PATTERN = re.compile(r"<(iframe|div|img|span)\b", re.IGNORECASE)

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.code_depth = 0
        self.matches: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in ("code", "pre"):
            self.code_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("code", "pre") and self.code_depth > 0:
            self.code_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.code_depth == 0:
            for match in self._PATTERN.finditer(data):
                self.matches.append(match.group(0))


def has_escaped_raw_html(page_html: str) -> bool:
    """Return True if escaped raw HTML tags appear in prose outside code blocks."""
    checker = _EscapedHtmlChecker()
    checker.feed(page_html)
    checker.close()
    return bool(checker.matches)


# ---------------------------------------------------------------------------
# Atom feed & Sitemap generation
# ---------------------------------------------------------------------------


def _xml_text(s: str) -> str:
    return html.escape(s, quote=False)


def _xml_attr(s: str) -> str:
    return html.escape(s, quote=True)


def _rfc3339(date_iso: str) -> str:
    return f"{date_iso}T00:00:00Z"


def generate_atom_feed(
    posts: list[dict[str, Any]],
    site_dir: Path,
    site_url: str = SITE_URL,
) -> str:
    """Generate and XML-validate the full-content Atom feed."""
    base = site_url.rstrip("/")
    entry_dates = [post.get("updated") or post["date"] for post in posts]
    feed_updated = _rfc3339(max(entry_dates)) if entry_dates else _rfc3339("2000-01-01")

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<?xml-stylesheet href="/atom.xsl" type="text/xsl"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"  <title>{_xml_text(SITE_TITLE)}</title>",
        f'  <link href="{_xml_attr(base + "/atom.xml")}" rel="self"/>',
        f'  <link href="{_xml_attr(base + "/")}" rel="alternate"/>',
        f"  <id>{_xml_text(base + '/atom.xml')}</id>",
        f"  <updated>{feed_updated}</updated>",
        f"  <author><name>{_xml_text(AUTHOR_NAME)}</name>"
        f"<email>{_xml_text(AUTHOR_EMAIL)}</email></author>",
    ]

    for post in posts:
        url = base + post["url"]
        published = post["date"]
        updated = post.get("updated") or published
        summary = post.get("description") or post["title"]
        lines.extend(
            [
                "  <entry>",
                f"    <title>{_xml_text(post['title'])}</title>",
                f'    <link href="{_xml_attr(url)}" rel="alternate"/>',
                f"    <id>{_xml_text(url)}</id>",
                f"    <published>{_rfc3339(published)}</published>",
                f"    <updated>{_rfc3339(updated)}</updated>",
            ]
        )
        for tag in post.get("tags", []):
            lines.append(f'    <category term="{_xml_attr(str(tag))}"/>')
        lines.append(f"    <summary>{_xml_text(summary)}</summary>")

        post_path = site_dir / "posts" / f"{post['slug']}.html"
        if post_path.is_file():
            content = extract_feed_content(post_path.read_text(encoding="utf-8"), site_url=base)
            if content:
                lines.append(f'    <content type="html">{_xml_text(content)}</content>')
        lines.append("  </entry>")

    lines.append("</feed>")
    xml_str = "\n".join(lines) + "\n"
    try:
        ET.fromstring(xml_str)
    except ET.ParseError as exc:
        raise BuildError(f"Generated atom.xml is not well-formed XML: {exc}") from exc
    return xml_str


def generate_sitemap(
    posts: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    site_url: str = SITE_URL,
) -> str:
    """Generate and XML-validate sitemap.xml (excluding 404)."""
    base = site_url.rstrip("/")
    entry_dates = [post.get("updated") or post["date"] for post in posts]
    latest_date = max(entry_dates) if entry_dates else None

    entries: list[tuple[str, str | None]] = [
        (f"{base}/", latest_date),
        (f"{base}/archive.html", latest_date),
    ]

    for page in sorted(pages, key=lambda p: p["name"]):
        if page["name"] == "404":
            continue
        entries.append((f"{base}/{page['name']}.html", page.get("updated") or page.get("date")))

    for post in posts:
        entries.append((f"{base}{post['url']}", post.get("updated") or post["date"]))

    tag_latest: dict[str, str] = {}
    for post in posts:
        post_lastmod = post.get("updated") or post["date"]
        for tag in post.get("tags", []):
            if tag not in tag_latest or post_lastmod > tag_latest[tag]:
                tag_latest[tag] = post_lastmod

    for tag in sorted(tag_latest):
        entries.append((f"{base}/tags/{slugify(tag)}.html", tag_latest[tag]))

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, lastmod in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{_xml_text(loc)}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{_xml_text(lastmod)}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    xml_str = "\n".join(lines) + "\n"
    try:
        ET.fromstring(xml_str)
    except ET.ParseError as exc:
        raise BuildError(f"Generated sitemap.xml is not well-formed XML: {exc}") from exc
    return xml_str


# ---------------------------------------------------------------------------
# Subprocess runners (Pandoc & Typst) + incremental cache
# ---------------------------------------------------------------------------


def _sha256_bytes(*chunks: bytes) -> str:
    h = hashlib.sha256()
    for chunk in chunks:
        h.update(chunk)
    return h.hexdigest()


def _atomic_write_text(dst: Path, content: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dst.name}.", dir=dst.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_name, dst)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def _pandoc_version_signature() -> bytes:
    proc = subprocess.run(["pandoc", "--version"], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise BuildError(f"Failed to run pandoc --version:\n{proc.stderr or proc.stdout}")
    first_line = proc.stdout.splitlines()[0] if proc.stdout else ""
    return first_line.encode("utf-8")


def convert_body(
    md_path: Path,
    cache_bodies: Path,
    lua_filter: Path,
    shared_key: bytes,
) -> bool:
    """Convert one Markdown file to `.cache/bodies/<stem>.typ`.

    Returns True on cache hit, False if Pandoc ran.
    """
    stem = md_path.stem
    dst_typ = cache_bodies / f"{stem}.typ"
    dst_hash = cache_bodies / f"{stem}.sha256"

    cache_key = _sha256_bytes(shared_key, b"\0", md_path.read_bytes())
    if dst_typ.is_file() and dst_hash.is_file():
        if dst_hash.read_text(encoding="utf-8").strip() == cache_key:
            return True

    proc = subprocess.run(
        [
            "pandoc",
            str(md_path),
            "--from",
            "markdown-raw_attribute",
            "--to",
            "typst",
            "--shift-heading-level-by=-1",
            "--wrap=none",
            "--lua-filter",
            str(lua_filter),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise BuildError(f"FAIL pandoc {md_path}\n{proc.stderr or proc.stdout}")

    _atomic_write_text(dst_typ, proc.stdout)
    _atomic_write_text(dst_hash, cache_key + "\n")
    return False


def compile_typst_html(root: Path, src: Path, extra_args: list[str]) -> str:
    """Compile a Typst file to HTML, failing on any unexpected warning."""
    with tempfile.NamedTemporaryFile(
        prefix="typst-", suffix=".html", delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        proc = subprocess.run(
            [
                "typst",
                "compile",
                "--root",
                str(root),
                "--features",
                "html",
                "--format",
                "html",
                *extra_args,
                str(src),
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        diag = proc.stdout + proc.stderr
        if proc.returncode != 0:
            raise BuildError(f"FAIL {src}\n{diag}")

        unexpected = [
            line
            for line in diag.splitlines()
            if line.strip()
            and not line.startswith("warning: html export is under active development")
            and not line.startswith(" = hint:")
        ]
        if unexpected:
            raise BuildError(f"FAIL (warnings) {src}\n" + "\n".join(unexpected))

        return tmp_path.read_text(encoding="utf-8")
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _run_parallel(jobs: int, fn: Any, items: list[Any]) -> list[Any]:
    if not items:
        return []
    if jobs <= 1 or len(items) == 1:
        return [fn(item) for item in items]
    results: list[Any] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        future_map = {pool.submit(fn, item): idx for idx, item in enumerate(items)}
        for fut in as_completed(future_map):
            results[future_map[fut]] = fut.result()
    return results


# ---------------------------------------------------------------------------
# Metadata collection
# ---------------------------------------------------------------------------


def collect_posts(post_paths: list[Path]) -> list[dict[str, Any]]:
    """Parse all post frontmatters and return records sorted newest-first."""
    posts: list[dict[str, Any]] = []
    for path in post_paths:
        slug = path.stem
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"), source=str(path))
        title = fm.get("title")
        date = fm.get("date")
        if not title or not date:
            raise BuildError(f"{path}: frontmatter must define 'title' and 'date'")
        date_str = str(date)
        if not _DATE_RE.fullmatch(date_str):
            raise BuildError(f"{path}: invalid date {date_str!r} (expected YYYY-MM-DD)")

        updated = fm.get("updated")
        updated_str: str | None = None
        if updated is not None:
            updated_str = str(updated)
            if not _DATE_RE.fullmatch(updated_str):
                raise BuildError(
                    f"{path}: invalid updated date {updated_str!r} (expected YYYY-MM-DD)"
                )

        raw_tags = fm.get("tags")
        if raw_tags is None:
            tags: list[str] = []
        elif isinstance(raw_tags, list):
            tags = [str(t) for t in raw_tags]
        else:
            raise BuildError(f"{path}: 'tags' must be a list, got {type(raw_tags).__name__}")

        record: dict[str, Any] = {
            "slug": slug,
            "url": f"/posts/{slug}.html",
            "title": str(title),
            "date": date_str,
            "author": str(fm.get("author") or AUTHOR_DEFAULT),
            "description": fm.get("description"),
            "tags": tags,
            "reading_time": estimate_reading_time(body),
        }
        if updated_str is not None:
            record["updated"] = updated_str
        posts.append(record)

    # Sort newest first; deterministic tie-break on slug descending.
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


def collect_pages(page_paths: list[Path]) -> list[dict[str, Any]]:
    """Parse all standalone page frontmatters."""
    pages: list[dict[str, Any]] = []
    for path in sorted(page_paths):
        name = path.stem
        fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"), source=str(path))
        title = fm.get("title")
        if not title:
            raise BuildError(f"{path}: frontmatter must define 'title'")
        pages.append(
            {
                "name": name,
                "path": path,
                "title": str(title),
                "description": str(fm.get("description") or f"{title} — {SITE_TITLE}"),
                "date": str(fm["date"]) if fm.get("date") else None,
                "updated": str(fm["updated"]) if fm.get("updated") else None,
            }
        )
    return pages


# ---------------------------------------------------------------------------
# Atomic directory swap
# ---------------------------------------------------------------------------


def atomic_swap_dir(staging: Path, target: Path) -> None:
    """Swap `staging` directory into `target` with minimal downtime and rollback."""
    if not target.exists():
        os.rename(staging, target)
        return

    backup = target.parent / f".{target.name}.old.{os.getpid()}"
    if backup.exists():
        shutil.rmtree(backup)

    os.rename(target, backup)
    try:
        os.rename(staging, target)
    except BaseException:
        os.rename(backup, target)
        raise
    else:
        shutil.rmtree(backup, ignore_errors=True)


# ---------------------------------------------------------------------------
# Main build pipeline
# ---------------------------------------------------------------------------


def _resolve_jobs(cli_jobs: int | None) -> int:
    if cli_jobs is not None:
        return max(1, cli_jobs)
    env_jobs = os.environ.get("JOBS")
    if env_jobs:
        try:
            return max(1, int(env_jobs))
        except ValueError as exc:
            raise BuildError(f"Invalid JOBS={env_jobs!r}: expected positive integer") from exc
    return max(1, os.cpu_count() or 4)


def run_optimize_images(
    root: Path,
    jobs: int,
    static_dir: Path,
    staging_dir: Path,
    cache_images: Path,
    manifest_path: Path,
) -> dict[str, dict[str, Any]]:
    """Run scripts/optimize-images.py via uv (or python3 with Pillow) and load manifest."""
    optimizer = root / "scripts" / "optimize-images.py"
    if not optimizer.is_file():
        return {}
    cmd_args = [
        "--jobs",
        str(jobs),
        str(static_dir),
        str(staging_dir),
        str(cache_images),
        str(manifest_path),
    ]
    uv_bin = shutil.which("uv")
    if uv_bin:
        cmd = [uv_bin, "run", "--quiet", str(optimizer), *cmd_args]
    else:
        pil_check = subprocess.run(
            [sys.executable, "-c", "import PIL"],
            capture_output=True,
            check=False,
        )
        if pil_check.returncode == 0:
            cmd = [sys.executable, str(optimizer), *cmd_args]
        else:
            raise BuildError(
                "FAIL: image optimization requires uv (https://docs.astral.sh/uv/) "
                "or python3 with Pillow\n"
                "Install uv: brew install uv  "
                "(or: curl -LsSf https://astral.sh/uv/install.sh | sh)"
            )
    proc = subprocess.run(cmd, check=False)
    if proc.returncode != 0:
        raise BuildError(f"FAIL image optimization (exit {proc.returncode})")
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"FAIL: could not read image manifest {manifest_path}: {exc}") from exc


def build_site(root: Path, jobs: int, clean: bool = False) -> Path:
    """Run the full site build and atomically publish into `<root>/_site`."""
    out_dir = root / "_site"
    cache_dir = root / ".cache"
    cache_bodies = cache_dir / "bodies"
    cache_images = cache_dir / "images"
    image_manifest_path = cache_dir / "image-manifest.json"
    static_dir = root / "static"
    lua_filter = root / "scripts" / "body-filter.lua"

    if clean:
        print("==> Cleaning cache")
        shutil.rmtree(cache_dir, ignore_errors=True)

    cache_bodies.mkdir(parents=True, exist_ok=True)
    cache_images.mkdir(parents=True, exist_ok=True)

    staging = Path(tempfile.mkdtemp(prefix="_site.tmp.", dir=root))
    try:
        (staging / "posts").mkdir(parents=True, exist_ok=True)
        (staging / "tags").mkdir(parents=True, exist_ok=True)

        print("==> Copying static files")
        shutil.copytree(static_dir, staging, dirs_exist_ok=True)

        image_manifest: dict[str, dict[str, Any]] = {}
        if (root / "scripts" / "optimize-images.py").is_file():
            print("==> Optimizing images")
            image_manifest = run_optimize_images(
                root, jobs, static_dir, staging, cache_images, image_manifest_path
            )

        # Fingerprint the stylesheet so deploys never pair new HTML with stale CSS.
        css_src = static_dir / "css" / "site.css"
        css_hash = hashlib.sha256(css_src.read_bytes()).hexdigest()[:8]
        css_href = f"/css/site.{css_hash}.css"
        shutil.copyfile(staging / "css" / "site.css", staging / css_href.lstrip("/"))

        post_paths = sorted((root / "posts").glob("*.md"))
        page_paths = sorted((root / "pages").glob("*.md"))
        all_md = post_paths + page_paths

        # Prune stale cached bodies from deleted/renamed markdown files.
        valid_stems = {p.stem for p in all_md}
        for cached in cache_bodies.iterdir():
            if cached.suffix in (".typ", ".sha256") and cached.stem not in valid_stems:
                cached.unlink(missing_ok=True)

        print("==> Converting markdown bodies with pandoc")
        shared_key = _sha256_bytes(
            _pandoc_version_signature(),
            b"\0markdown-raw_attribute\0typst\0-1\0none\0",
            lua_filter.read_bytes(),
        ).encode("ascii")
        hits = _run_parallel(
            jobs,
            lambda md: convert_body(md, cache_bodies, lua_filter, shared_key),
            all_md,
        )
        hit_count = sum(1 for h in hits if h)
        if hit_count:
            print(f"    ({hit_count}/{len(all_md)} cached)")

        print("==> Collecting post metadata")
        posts = collect_posts(post_paths)
        pages = collect_pages(page_paths)

        # Verify tag slugs are non-empty and collision-free.
        tag_slugs: dict[str, str] = {}
        unique_tags = sorted({tag for post in posts for tag in post["tags"]})
        for tag in unique_tags:
            tslug = slugify(tag)
            if not tslug:
                raise BuildError(f"Tag {tag!r} produces an empty slug")
            if tslug in tag_slugs and tag_slugs[tslug] != tag:
                raise BuildError(
                    f"Tags {tag_slugs[tslug]!r} and {tag!r} collide on slug {tslug!r}"
                )
            tag_slugs[tslug] = tag

        _atomic_write_text(
            cache_dir / "posts.json",
            json.dumps(posts, indent=2, ensure_ascii=False) + "\n",
        )

        print(f"==> Building posts ({len(posts)})")

        def _build_post(post: dict[str, Any]) -> None:
            slug = post["slug"]
            raw_html = compile_typst_html(
                root,
                root / "lib" / "post.typ",
                [
                    "--input",
                    f"path=/posts/{slug}.md",
                    "--input",
                    f"body=/.cache/bodies/{slug}.typ",
                    "--input",
                    f"slug={slug}",
                ],
            )
            meta = PageMeta(
                title=post["title"],
                description=post.get("description") or post["title"],
                canonical_url=f"{SITE_URL}{post['url']}",
                og_type="article",
                published_time=post["date"],
                modified_time=post.get("updated"),
                add_heading_anchors=True,
            )
            rendered = postprocess_html(raw_html, css_href, meta, image_manifest)
            (staging / "posts" / f"{slug}.html").write_text(rendered, encoding="utf-8")

        _run_parallel(jobs, _build_post, posts)

        print(f"==> Building pages ({len(pages)})")

        def _build_page(page: dict[str, Any]) -> None:
            name = page["name"]
            raw_html = compile_typst_html(
                root,
                root / "lib" / "page.typ",
                [
                    "--input",
                    f"path=/pages/{name}.md",
                    "--input",
                    f"body=/.cache/bodies/{name}.typ",
                ],
            )
            meta = PageMeta(
                title=page["title"],
                description=page["description"],
                canonical_url=f"{SITE_URL}/{name}.html",
                og_type="website",
                noindex=(name == "404"),
                add_heading_anchors=(name != "404"),
            )
            rendered = postprocess_html(raw_html, css_href, meta, image_manifest)
            (staging / f"{name}.html").write_text(rendered, encoding="utf-8")

        _run_parallel(jobs, _build_page, pages)

        print(f"==> Building listings ({2 + len(unique_tags)})")
        listing_specs: list[tuple[str, str | None]] = [("index", None), ("archive", None)]
        listing_specs.extend(("tag", tag) for tag in unique_tags)

        def _build_listing(spec: tuple[str, str | None]) -> None:
            kind, tag = spec
            if kind == "tag":
                assert tag is not None
                tslug = slugify(tag)
                args = ["--input", "kind=tag", "--input", f"tag={tag}"]
                dst = staging / "tags" / f"{tslug}.html"
                meta = PageMeta(
                    title=f'Posts tagged "{tag}"',
                    description=TAG_DESCRIPTION_TEMPLATE.format(tag=tag),
                    canonical_url=f"{SITE_URL}/tags/{tslug}.html",
                    og_type="website",
                    add_heading_anchors=False,
                )
            elif kind == "index":
                args = ["--input", "kind=index"]
                dst = staging / "index.html"
                meta = PageMeta(
                    title=SITE_TITLE,
                    description=INDEX_DESCRIPTION,
                    canonical_url=f"{SITE_URL}/",
                    og_type="website",
                    add_heading_anchors=False,
                )
            else:
                args = ["--input", "kind=archive"]
                dst = staging / "archive.html"
                meta = PageMeta(
                    title="Archive",
                    description=ARCHIVE_DESCRIPTION,
                    canonical_url=f"{SITE_URL}/archive.html",
                    og_type="website",
                    add_heading_anchors=False,
                )
            raw_html = compile_typst_html(root, root / "lib" / "listing.typ", args)
            rendered = postprocess_html(raw_html, css_href, meta, image_manifest)
            dst.write_text(rendered, encoding="utf-8")

        _run_parallel(jobs, _build_listing, listing_specs)

        print("==> Checking for silently escaped raw HTML")
        bad_html: list[str] = []
        for html_file in sorted(staging.rglob("*.html")):
            if has_escaped_raw_html(html_file.read_text(encoding="utf-8")):
                bad_html.append(str(html_file.relative_to(staging)))
        if bad_html:
            raise BuildError(
                "FAIL: escaped raw HTML outside code blocks (multi-line tag in a post?)\n"
                + "\n".join(bad_html)
            )

        print("==> Generating atom.xml and sitemap.xml")
        atom_xml = generate_atom_feed(posts, staging)
        (staging / "atom.xml").write_text(atom_xml, encoding="utf-8")

        sitemap_xml = generate_sitemap(posts, pages)
        (staging / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")

        # Validate atom.xsl as well if present.
        atom_xsl = staging / "atom.xsl"
        if atom_xsl.is_file():
            try:
                ET.fromstring(atom_xsl.read_text(encoding="utf-8"))
            except ET.ParseError as exc:
                raise BuildError(f"static/atom.xsl is not well-formed XML: {exc}") from exc

        atomic_swap_dir(staging, out_dir)
        print(f"==> Done: {out_dir}")
        return out_dir
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build storopoli.com static site.")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Wipe .cache/ before building (forces full Pandoc re-conversion).",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help="Parallel worker count (defaults to $JOBS or CPU count).",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    try:
        jobs = _resolve_jobs(args.jobs)
        build_site(root=root, jobs=jobs, clean=args.clean)
    except BuildError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
