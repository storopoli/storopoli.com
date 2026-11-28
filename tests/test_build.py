"""Unit tests for scripts/build.py, frontmatter, HTML postprocessing, feeds, and sitemap."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_build_module():
    spec = importlib.util.spec_from_file_location("site_build", REPO_ROOT / "scripts" / "build.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


build = _load_build_module()

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class SlugifyTests(unittest.TestCase):
    def test_slugify_normalizes_ascii_and_punctuation(self) -> None:
        cases = {
            "math": "math",
            "web development": "web-development",
            "Machine Learning": "machine-learning",
            "foo_bar/baz!": "foo-bar-baz",
            "  --Rust & Zig--  ": "rust-zig",
            "C++20": "c-20",
            "zero-knowledge_proofs": "zero-knowledge-proofs",
            "---": "",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(build.slugify(raw), expected)

    def test_template_slugify_aligned(self) -> None:
        tpl = (REPO_ROOT / "lib" / "template.typ").read_text(encoding="utf-8")
        self.assertIn(
            '#let slugify(s) = lower(s).replace(regex("[^a-z0-9]+"), "-").trim("-")',
            tpl,
        )


class FrontmatterParserTests(unittest.TestCase):
    def test_all_real_posts_and_pages_parse_accurately(self) -> None:
        post_paths = sorted((REPO_ROOT / "posts").glob("*.md"))
        page_paths = sorted((REPO_ROOT / "pages").glob("*.md"))
        self.assertGreaterEqual(len(post_paths), 22)
        self.assertEqual([p.stem for p in page_paths], ["404", "about", "contact"])

        bib_posts: list[str] = []
        no_toc_posts: list[str] = []
        updated_posts: dict[str, str] = {}

        for path in post_paths:
            with self.subTest(path=path.name):
                fm, body = build.parse_frontmatter(path.read_text(encoding="utf-8"), str(path))
                self.assertIsInstance(fm.get("title"), str)
                self.assertTrue(fm["title"].strip())
                self.assertRegex(str(fm.get("date")), r"^\d{4}-\d{2}-\d{2}$")
                self.assertEqual(fm.get("author"), "Jose Storopoli")
                self.assertIsInstance(fm.get("description"), str)
                self.assertTrue(fm["description"].strip(), f"{path.name} missing description")
                self.assertIsInstance(fm.get("tags"), list)
                self.assertGreater(len(fm["tags"]), 0)
                for tag in fm["tags"]:
                    self.assertIsInstance(tag, str)
                    self.assertTrue(build.slugify(tag))
                self.assertTrue(body.strip())

                if fm.get("bib") is True:
                    bib_posts.append(path.stem)
                if fm.get("no-toc") is True:
                    no_toc_posts.append(path.stem)
                if "updated" in fm:
                    updated_posts[path.stem] = fm["updated"]

                # Reading time should be sensible (1..40 min)
                rt = build.estimate_reading_time(body)
                self.assertGreaterEqual(rt, 1)
                self.assertLessEqual(rt, 40)

        self.assertEqual(
            bib_posts,
            [
                "2023-11-23-lindley_paradox",
                "2024-06-08-zkp",
                "2024-11-15-taproot",
                "2025-02-10-bitvm",
                "2025-04-07-randomness",
            ],
        )
        self.assertEqual(
            no_toc_posts,
            [
                "2025-08-09-letter-to-my-son",
                "2025-11-09-bifi",
            ],
        )
        self.assertEqual(updated_posts.get("2026-01-04-evm-yubikeys"), "2026-11-25")

        for path in page_paths:
            with self.subTest(path=path.name):
                fm, body = build.parse_frontmatter(path.read_text(encoding="utf-8"), str(path))
                self.assertIsInstance(fm.get("title"), str)
                self.assertTrue(fm["title"].strip())
                self.assertIsInstance(fm.get("description"), str)
                self.assertTrue(fm["description"].strip(), f"{path.name} missing description")
                self.assertTrue(body.strip())

        # Specifically verify pages/about.md keeps its body past the horizontal rule `---`.
        about_fm, about_body = build.parse_frontmatter(
            (REPO_ROOT / "pages" / "about.md").read_text(encoding="utf-8"),
            "pages/about.md",
        )
        self.assertEqual(about_fm["title"], "About")
        self.assertIn("## Curriculum Vitae", about_body)

    def test_crlf_bom_and_extra_thematic_breaks(self) -> None:
        doc = (
            "\ufeff---\r\n"
            'title: "Hello: world"\r\n'
            "date: 2025-01-02\r\n"
            "updated: 2025-03-04\r\n"
            "bib: true # inline comment\r\n"
            "no-toc: false\r\n"
            "toc-depth: 2\r\n"
            "tags:\r\n"
            "  - math\r\n"
            '  - "web development"\r\n'
            "  - 'it''s fine'\r\n"
            "---\r\n"
            "First paragraph\r\n"
            "\r\n"
            "---\r\n"
            "\r\n"
            "Second paragraph\r\n"
        )
        fm, body = build.parse_frontmatter(doc, "crlf.md")
        self.assertEqual(fm["title"], "Hello: world")
        self.assertEqual(fm["date"], "2025-01-02")
        self.assertEqual(fm["updated"], "2025-03-04")
        self.assertIs(fm["bib"], True)
        self.assertIs(fm["no-toc"], False)
        self.assertEqual(fm["toc-depth"], 2)
        self.assertEqual(fm["tags"], ["math", "web development", "it's fine"])
        self.assertIn("First paragraph", body)
        self.assertIn("Second paragraph", body)

    def test_inline_list_with_quotes_commas_and_empty(self) -> None:
        doc = (
            "---\n"
            'tags: ["a, b", \'c, d\', plain]\n'
            "empty: []\n"
            "nullable: null\n"
            'sharp: "C# guide" # trailing comment\n'
            "---\n"
            "body\n"
        )
        fm, _ = build.parse_frontmatter(doc)
        self.assertEqual(fm["tags"], ["a, b", "c, d", "plain"])
        self.assertEqual(fm["empty"], [])
        self.assertIsNone(fm["nullable"])
        self.assertEqual(fm["sharp"], "C# guide")

    def test_invalid_frontmatter_and_dates_raise(self) -> None:
        with self.assertRaises(ValueError):
            build.parse_frontmatter("no frontmatter here")
        with self.assertRaises(ValueError):
            build.parse_frontmatter("---\ntitle: Unclosed\n")
        with self.assertRaises(ValueError):
            build.parse_frontmatter("---\ndate: 2024-02-31\n---\nbody\n")

    def test_collect_posts_sorts_newest_first(self) -> None:
        posts = build.collect_posts(sorted((REPO_ROOT / "posts").glob("*.md")))
        dates = [p["date"] for p in posts]
        self.assertEqual(dates, sorted(dates, reverse=True))
        self.assertEqual(posts[0]["slug"], "2026-01-04-evm-yubikeys")
        self.assertEqual(posts[0]["updated"], "2026-11-25")
        self.assertGreaterEqual(posts[0]["reading_time"], 1)


SAMPLE_TYPST_POST_HTML = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Jose Storopoli, PhD - Sample Post</title>
    <meta name="description" content="Sample description.">
  </head>
  <body>
    <header class="post-header"><nav><a href="/">Home</a></nav></header>
    <main>
      <article>
        <h1>Sample Post</h1>
        <div class="post-meta">
          <time datetime="2026-01-04">2026-01-04</time>
          <span class="post-updated">updated <time datetime="2026-11-25">2026-11-25</time></span>
          <span class="reading-time">5 min read</span>
        </div>
        <details id="table-of-contents" class="toc">
          <summary>Contents</summary>
          <nav><ol><li><a href="#intro">Intro</a></li></ol></nav>
        </details>
        <section>
          <h2 id="intro">Intro</h2>
          <p>See <a href="/posts/other.html">other</a> and <a href="#fn1" role="doc-noteref">1</a>.</p>
          <p>Inline math: <math><mi>x</mi></math>.</p>
          <math display="block"><msup><mi>a</mi><mn>2</mn></msup></math>
          <h3 id="code-sample">Code</h3>
          <pre><code data-lang="rust"><span style="color: #d73948">let</span> <span style="color: #4b69c6">html</span> = <span style="color: #198810">"&lt;a href=\"/do-not-rewrite\"&gt;&lt;span style=\"color: #123456\"&gt;x&lt;/span&gt;&lt;/a&gt;"</span>;</code></pre>
          <pre><code>plain block without lang</code></pre>
          <table><thead><tr><th><math><mi>b</mi></math></th><th><math><msup><mi>b</mi><mn>1</mn></msup><mo>mod</mo><mn>7</mn></math></th></tr></thead><tbody><tr><td>2</td><td>2</td></tr></tbody></table>
          <figure><img src="/images/demo.png" alt="Demo" loading="lazy"><figcaption>Demo</figcaption></figure>
          <figure><img src="/images/second.svg" alt="Second" loading="lazy"><figcaption>Second</figcaption></figure>
          <h4 id="sub">Sub</h4>
          <h2>No ID heading</h2>
          <h5 id="eyebrow">Eyebrow</h5>
        </section>
      </article>
      <nav class="post-nav" aria-label="Post navigation">
        <div class="post-nav-prev"><a href="/posts/2025-11-09-bifi.html" rel="prev"><span class="post-nav-label">← Previous</span><span class="post-nav-title">BiFi</span></a></div>
      </nav>
    </main>
    <footer>Footer</footer>
    <section role="doc-endnotes">
      <ol>
        <li id="fn1"><p>Note with <a href="/about.html">about link</a> and <span style="color: #74747c">// comment</span>.</p></li>
      </ol>
    </section>
  </body>
</html>
"""


class HtmlPostprocessorTests(unittest.TestCase):
    def test_postprocess_full_post(self) -> None:
        meta = build.PageMeta(
            title="Sample Post",
            description="Sample description.",
            canonical_url="https://storopoli.com/posts/sample.html",
            og_type="article",
            published_time="2026-01-04",
            modified_time="2026-11-25",
            add_heading_anchors=True,
        )
        image_manifest = {
            "/images/demo.png": {"width": 800, "height": 600, "webp": "/images/demo.webp"},
            "/images/second.svg": {"width": 400, "height": 300},
        }
        out = build.postprocess_html(
            SAMPLE_TYPST_POST_HTML, "/css/site.deadbeef.css", meta, image_manifest
        )

        # Head tags injected without duplicating <meta name="description">
        self.assertEqual(out.count('name="description"'), 1)
        self.assertIn('<link rel="stylesheet" href="/css/site.deadbeef.css">', out)
        self.assertIn('<link rel="canonical" href="https://storopoli.com/posts/sample.html">', out)
        self.assertIn('<meta property="og:site_name" content="Jose Storopoli, PhD">', out)
        self.assertIn('<meta property="og:title" content="Sample Post">', out)
        self.assertIn('<meta property="og:description" content="Sample description.">', out)
        self.assertIn('<meta property="og:url" content="https://storopoli.com/posts/sample.html">', out)
        self.assertIn('<meta property="og:type" content="article">', out)
        self.assertIn('<meta property="article:published_time" content="2026-01-04">', out)
        self.assertIn('<meta property="article:modified_time" content="2026-11-25">', out)
        self.assertIn('<meta name="twitter:card" content="summary">', out)
        self.assertIn('<meta name="twitter:title" content="Sample Post">', out)
        self.assertIn('<meta name="twitter:description" content="Sample description.">', out)

        # Endnotes relocated inside <article>, before <nav class="post-nav"> and <footer>
        endnotes_pos = out.index('<section role="doc-endnotes">')
        article_close_pos = out.index("</article>")
        nav_pos = out.index('<nav class="post-nav"')
        footer_pos = out.index("<footer>")
        self.assertLess(endnotes_pos, article_close_pos)
        self.assertLess(article_close_pos, nav_pos)
        self.assertLess(nav_pos, footer_pos)

        # Block math wrapped; inline math untouched
        self.assertIn('<div class="math-block"><math display="block">', out)
        self.assertIn("</math></div>", out)
        self.assertIn("Inline math: <math><mi>x</mi></math>.", out)

        # Syntax highlight tokens mapped (including inside endnotes) without tripping on code text
        self.assertIn('<span class="tok-red">let</span>', out)
        self.assertIn('<span class="tok-blue">html</span>', out)
        self.assertIn('<span class="tok-green">"&lt;a href=', out)
        self.assertIn('<span class="tok-gray">// comment</span>', out)

        # Language-tagged <pre><code data-lang="..."> wrapped in .code-block + .code-lang;
        # untagged <pre><code> left unwrapped.
        self.assertIn(
            '<div class="code-block"><div class="code-lang">rust</div><pre><code data-lang="rust">',
            out,
        )
        self.assertIn("</code></pre></div>", out)
        self.assertIn("<pre><code>plain block without lang</code></pre>", out)
        self.assertEqual(out.count('class="code-block"'), 1)

        # Tables inside <main> wrapped in .table-wrap
        self.assertIn(
            '<div class="table-wrap"><table><thead><tr><th><math><mi>b</mi></math></th>',
            out,
        )
        self.assertIn("</tbody></table></div>", out)

        # Section anchors injected on h2-h4 with id, NOT on h2 without id or h5
        self.assertIn(
            '<h2 id="intro">Intro<a class="heading-anchor" href="#intro" '
            'aria-label="Link to this section">#</a></h2>',
            out,
        )
        self.assertIn(
            '<h3 id="code-sample">Code<a class="heading-anchor" href="#code-sample" '
            'aria-label="Link to this section">#</a></h3>',
            out,
        )
        self.assertIn(
            '<h4 id="sub">Sub<a class="heading-anchor" href="#sub" '
            'aria-label="Link to this section">#</a></h4>',
            out,
        )
        self.assertIn("<h2>No ID heading</h2>", out)
        self.assertIn('<h5 id="eyebrow">Eyebrow</h5>', out)

        # Image enhancement: first image gets fetchpriority="high" (no loading="lazy")
        # and WebP <picture> wrapper; second keeps loading="lazy" and gets dimensions.
        self.assertIn(
            '<picture><source srcset="/images/demo.webp" type="image/webp">'
            '<img src="/images/demo.png" alt="Demo" fetchpriority="high" '
            'width="800" height="600" decoding="async"></picture>',
            out,
        )
        self.assertIn(
            '<img src="/images/second.svg" alt="Second" loading="lazy" '
            'width="400" height="300" decoding="async">',
            out,
        )

    def test_postprocess_injects_description_when_missing_and_noindex_on_404(self) -> None:
        raw = "<!DOCTYPE html><html><head><title>404</title></head><body><main><h1>404</h1></main></body></html>"
        meta = build.PageMeta(
            title="Page Not Found",
            description="Missing page.",
            canonical_url="https://storopoli.com/404.html",
            og_type="website",
            noindex=True,
            add_heading_anchors=False,
        )
        out = build.postprocess_html(raw, "/css/site.12345678.css", meta)
        self.assertIn('<meta name="description" content="Missing page.">', out)
        self.assertIn('<meta name="robots" content="noindex">', out)

    def test_postprocess_endnotes_fallback_to_main_without_article(self) -> None:
        raw = (
            "<!DOCTYPE html><html><head><title>About</title></head><body>"
            "<main><p>Hi</p></main><footer>Foot</footer>"
            '<section role="doc-endnotes"><ol><li>Note</li></ol></section>'
            "</body></html>"
        )
        meta = build.PageMeta(
            title="About",
            description="About page.",
            canonical_url="https://storopoli.com/about.html",
        )
        out = build.postprocess_html(raw, "/css/site.12345678.css", meta)
        self.assertLess(out.index('<section role="doc-endnotes">'), out.index("</main>"))

    def test_postprocess_fails_on_unmapped_highlight_color(self) -> None:
        raw = (
            "<!DOCTYPE html><html><head><title>T</title></head><body>"
            '<main><pre><code><span style="color: #abcdef">tok</span></code></pre></main>'
            "</body></html>"
        )
        meta = build.PageMeta(title="T", description="D", canonical_url="https://storopoli.com/t.html")
        with self.assertRaises(build.BuildError) as ctx:
            build.postprocess_html(raw, "/css/site.css", meta)
        self.assertIn("#abcdef", str(ctx.exception))

    def test_postprocess_fails_without_head(self) -> None:
        meta = build.PageMeta(title="T", description="D", canonical_url="https://storopoli.com/t.html")
        with self.assertRaises(build.BuildError):
            build.postprocess_html("<html><body><main></main></body></html>", "/css/site.css", meta)

    def test_postprocess_code_block_and_table_wrap_edge_cases(self) -> None:
        raw = (
            "<!DOCTYPE html><html><head><title>T</title></head><body><main>"
            '<pre>\n  <code data-lang="c++ &amp; rust">x</code></pre>'
            '<pre><code data-lang="   ">blank lang</code></pre>'
            "<pre>raw pre text</pre>"
            "<table><tbody><tr><td><table><tr><td>nested</td></tr></table></td></tr></tbody></table>"
            "</main></body></html>"
        )
        meta = build.PageMeta(title="T", description="D", canonical_url="https://storopoli.com/t.html")
        out = build.postprocess_html(raw, "/css/site.css", meta)

        self.assertIn(
            '<div class="code-block"><div class="code-lang">c++ &amp; rust</div>'
            '<pre>\n  <code data-lang="c++ &amp; rust">x</code></pre></div>',
            out,
        )
        self.assertIn('<pre><code data-lang="   ">blank lang</code></pre>', out)
        self.assertIn("<pre>raw pre text</pre>", out)
        self.assertEqual(out.count('class="code-block"'), 1)
        # Nested table must only be wrapped once on the outermost <table>
        self.assertEqual(out.count('class="table-wrap"'), 1)
        self.assertIn(
            '<div class="table-wrap"><table><tbody><tr><td><table><tr><td>nested</td></tr></table></td></tr></tbody></table></div>',
            out,
        )

    def test_extract_feed_content_unwraps_wrappers_preserving_inner_divs(self) -> None:
        page_html = (
            "<!DOCTYPE html><html><head></head><body><main><article>"
            "<h1>Title</h1>"
            '<div class="code-block"><div class="code-lang">rust</div>'
            '<pre><code data-lang="rust"><span class="tok-red">fn</span> main() {}</code></pre></div>'
            '<div class="table-wrap"><table><tbody><tr><td><div class="cell">ok</div></td></tr></tbody></table></div>'
            '<div class="embed-container"><iframe src="https://example.com"></iframe></div>'
            "</article></main></body></html>"
        )
        content = build.extract_feed_content(page_html)
        assert content is not None
        self.assertNotIn("code-block", content)
        self.assertNotIn("code-lang", content)
        self.assertNotIn("table-wrap", content)
        self.assertIn('<pre><code data-lang="rust"><span style="color: #af3029">fn</span> main() {}</code></pre>', content)
        self.assertIn('<table><tbody><tr><td><div class="cell">ok</div></td></tr></tbody></table>', content)
        self.assertIn('<div class="embed-container"><iframe src="https://example.com"></iframe></div>', content)

    def test_all_token_classes_match_feed_colors_and_css(self) -> None:
        css = (REPO_ROOT / "static" / "css" / "site.css").read_text(encoding="utf-8")
        for tok_cls in set(build.TOKEN_CLASSES.values()):
            self.assertIn(tok_cls, build.FEED_TOKEN_COLORS)
            light_hex = build.FEED_TOKEN_COLORS[tok_cls]
            self.assertRegex(
                css,
                rf"\.{re.escape(tok_cls)}\s*\{{\s*color:\s*(?:light-dark\()?{re.escape(light_hex)}",
            )


class EscapedRawHtmlCheckTests(unittest.TestCase):
    def test_detects_escaped_html_outside_code_only(self) -> None:
        self.assertTrue(
            build.has_escaped_raw_html("<main><p>&lt;div class='x'&gt;oops&lt;/div&gt;</p></main>")
        )
        self.assertTrue(
            build.has_escaped_raw_html("<main><p>&lt;iframe src='x'&gt;</p></main>")
        )
        self.assertFalse(
            build.has_escaped_raw_html(
                '<main><pre><code>&lt;div class="x"&gt;&lt;span&gt;ok&lt;/span&gt;&lt;/div&gt;</code></pre></main>'
            )
        )
        self.assertFalse(
            build.has_escaped_raw_html('<main><div class="real"><img src="/x.png"></div></main>')
        )


class AtomFeedAndSitemapTests(unittest.TestCase):
    def test_atom_feed_generation_and_code_safety(self) -> None:
        meta = build.PageMeta(
            title="Sample Post",
            description="Sample description.",
            canonical_url="https://storopoli.com/posts/sample.html",
            og_type="article",
            published_time="2026-01-04",
            modified_time="2026-11-25",
            add_heading_anchors=True,
        )
        image_manifest = {
            "/images/demo.png": {"width": 800, "height": 600, "webp": "/images/demo.webp"},
        }
        built_post_html = build.postprocess_html(
            SAMPLE_TYPST_POST_HTML, "/css/site.deadbeef.css", meta, image_manifest
        )

        posts = [
            {
                "slug": "sample",
                "url": "/posts/sample.html",
                "title": "Sample Post",
                "date": "2026-01-04",
                "updated": "2026-11-25",
                "author": "Jose Storopoli",
                "description": "Sample description.",
                "tags": ["rust", "web development"],
                "reading_time": 5,
            },
            {
                "slug": "older",
                "url": "/posts/older.html",
                "title": "Older Post",
                "date": "2025-05-01",
                "author": "Jose Storopoli",
                "description": "Older summary.",
                "tags": ["math"],
                "reading_time": 3,
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            site_dir = Path(tmpdir)
            (site_dir / "posts").mkdir()
            (site_dir / "posts" / "sample.html").write_text(built_post_html, encoding="utf-8")

            atom_xml = build.generate_atom_feed(posts, site_dir)

        self.assertIn('<?xml-stylesheet href="/atom.xsl" type="text/xsl"?>', atom_xml)
        root = ET.fromstring(atom_xml)
        self.assertEqual(root.findtext("atom:updated", namespaces=ATOM_NS), "2026-11-25T00:00:00Z")

        entries = root.findall("atom:entry", namespaces=ATOM_NS)
        self.assertEqual(len(entries), 2)

        first = entries[0]
        self.assertEqual(first.findtext("atom:published", namespaces=ATOM_NS), "2026-01-04T00:00:00Z")
        self.assertEqual(first.findtext("atom:updated", namespaces=ATOM_NS), "2026-11-25T00:00:00Z")
        cats = [el.attrib["term"] for el in first.findall("atom:category", namespaces=ATOM_NS)]
        self.assertEqual(cats, ["rust", "web development"])

        content = first.findtext("atom:content", namespaces=ATOM_NS)
        assert content is not None
        # Chrome stripped
        self.assertNotIn("<h1>", content)
        self.assertNotIn("post-meta", content)
        self.assertNotIn("table-of-contents", content)
        self.assertNotIn("post-nav", content)
        self.assertNotIn("heading-anchor", content)
        # Real links/images absolutized; <picture>/<source> unwrapped for feed readers
        self.assertNotIn("<picture", content)
        self.assertNotIn("<source", content)
        self.assertIn('href="https://storopoli.com/posts/other.html"', content)
        self.assertIn('src="https://storopoli.com/images/demo.png"', content)
        self.assertIn('href="https://storopoli.com/about.html"', content)
        self.assertIn('href="#fn1"', content)
        # Code block text containing href="/do-not-rewrite" MUST NOT be rewritten!
        self.assertIn('href="/do-not-rewrite"', content)
        self.assertNotIn("https://storopoli.com/do-not-rewrite", content)
        # Inline Flexoki WCAG AA light-mode colors applied to syntax highlight spans
        self.assertIn('<span style="color: #af3029">let</span>', content)
        self.assertIn('<span style="color: #205ea6">html</span>', content)
        self.assertIn('<span style="color: #575653">// comment</span>', content)
        self.assertNotIn("tok-red", content)
        # Layout wrappers (.code-block, .code-lang, .table-wrap) stripped/unwrapped cleanly
        self.assertNotIn("code-block", content)
        self.assertNotIn("code-lang", content)
        self.assertNotIn("table-wrap", content)
        self.assertIn('<pre><code data-lang="rust">', content)
        self.assertIn("<table><thead><tr><th><math><mi>b</mi></math></th>", content)

        # Second entry falls back to published date for <updated>
        second = entries[1]
        self.assertEqual(second.findtext("atom:published", namespaces=ATOM_NS), "2025-05-01T00:00:00Z")
        self.assertEqual(second.findtext("atom:updated", namespaces=ATOM_NS), "2025-05-01T00:00:00Z")

    def test_atom_xsl_is_valid_xml_and_lychee_safe(self) -> None:
        xsl_text = (REPO_ROOT / "static" / "atom.xsl").read_text(encoding="utf-8")
        ET.fromstring(xsl_text)
        # Avoid attribute value templates like href="{...}" that offline link checkers misread
        self.assertNotIn('href="{', xsl_text)
        self.assertIn('<xsl:attribute name="href">', xsl_text)

    def test_sitemap_xml_and_robots_txt(self) -> None:
        posts = build.collect_posts(sorted((REPO_ROOT / "posts").glob("*.md")))
        pages = build.collect_pages(sorted((REPO_ROOT / "pages").glob("*.md")))
        sitemap_xml = build.generate_sitemap(posts, pages)

        root = ET.fromstring(sitemap_xml)
        urls = {
            url.findtext("sm:loc", namespaces=SITEMAP_NS): url.findtext("sm:lastmod", namespaces=SITEMAP_NS)
            for url in root.findall("sm:url", namespaces=SITEMAP_NS)
        }
        self.assertEqual(urls["https://storopoli.com/"], "2026-11-25")
        self.assertEqual(urls["https://storopoli.com/archive.html"], "2026-11-25")
        self.assertIn("https://storopoli.com/about.html", urls)
        self.assertIn("https://storopoli.com/contact.html", urls)
        self.assertNotIn("https://storopoli.com/404.html", urls)
        self.assertEqual(
            urls["https://storopoli.com/posts/2026-01-04-evm-yubikeys.html"],
            "2026-11-25",
        )
        self.assertEqual(
            urls["https://storopoli.com/posts/2024-11-15-taproot.html"],
            "2024-11-15",
        )
        self.assertIn("https://storopoli.com/tags/web-development.html", urls)

        robots = (REPO_ROOT / "static" / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Sitemap: https://storopoli.com/sitemap.xml", robots)


class PipelineMechanicsTests(unittest.TestCase):
    def test_compile_typst_warning_filter(self) -> None:
        def fake_ok(cmd, **_kwargs):
            Path(cmd[-1]).write_text("<html><head></head><body></body></html>", encoding="utf-8")
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout="",
                stderr=(
                    "warning: html export is under active development and incomplete\n"
                    " = hint: its behaviour may change at any time\n"
                ),
            )

        with mock.patch.object(build.subprocess, "run", side_effect=fake_ok):
            out = build.compile_typst_html(REPO_ROOT, REPO_ROOT / "lib" / "page.typ", [])
            self.assertIn("<html>", out)

        def fake_warn(cmd, **_kwargs):
            Path(cmd[-1]).write_text("<html></html>", encoding="utf-8")
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout="",
                stderr=(
                    "warning: html export is under active development\n"
                    "warning: equation was ignored\n"
                ),
            )

        with mock.patch.object(build.subprocess, "run", side_effect=fake_warn):
            with self.assertRaises(build.BuildError) as ctx:
                build.compile_typst_html(REPO_ROOT, REPO_ROOT / "lib" / "page.typ", [])
            self.assertIn("equation was ignored", str(ctx.exception))

    def test_incremental_pandoc_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            md = root / "demo.md"
            md.write_text("---\ntitle: Demo\n---\nhello\n", encoding="utf-8")
            lua = root / "filter.lua"
            lua.write_text("-- filter", encoding="utf-8")
            cache_bodies = root / ".cache" / "bodies"
            cache_bodies.mkdir(parents=True)

            calls = 0

            def fake_pandoc(cmd, **_kwargs):
                nonlocal calls
                calls += 1
                return subprocess.CompletedProcess(cmd, 0, stdout="= Demo\n", stderr="")

            with mock.patch.object(build.subprocess, "run", side_effect=fake_pandoc):
                hit1 = build.convert_body(md, cache_bodies, lua, b"v1")
                hit2 = build.convert_body(md, cache_bodies, lua, b"v1")
                md.write_text("---\ntitle: Demo\n---\nchanged\n", encoding="utf-8")
                hit3 = build.convert_body(md, cache_bodies, lua, b"v1")
                hit4 = build.convert_body(md, cache_bodies, lua, b"v2")

            self.assertFalse(hit1)
            self.assertTrue(hit2)
            self.assertFalse(hit3)
            self.assertFalse(hit4)
            self.assertEqual(calls, 3)

    def test_atomic_swap_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "_site"
            staging1 = root / "_site.tmp.1"
            staging1.mkdir()
            (staging1 / "index.html").write_text("v1", encoding="utf-8")

            build.atomic_swap_dir(staging1, target)
            self.assertEqual((target / "index.html").read_text(encoding="utf-8"), "v1")
            self.assertFalse(staging1.exists())

            staging2 = root / "_site.tmp.2"
            staging2.mkdir()
            (staging2 / "index.html").write_text("v2", encoding="utf-8")
            build.atomic_swap_dir(staging2, target)
            self.assertEqual((target / "index.html").read_text(encoding="utf-8"), "v2")
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["_site"])

    def test_end_to_end_build_site_with_mocked_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "posts").mkdir()
            (root / "pages").mkdir()
            (root / "lib").mkdir()
            (root / "scripts").mkdir()
            (root / "static" / "css").mkdir(parents=True)

            (root / "static" / "css" / "site.css").write_text("body { color: #100f0f; }\n", encoding="utf-8")
            shutil.copyfile(REPO_ROOT / "static" / "atom.xsl", root / "static" / "atom.xsl")
            shutil.copyfile(REPO_ROOT / "static" / "robots.txt", root / "static" / "robots.txt")
            (root / "scripts" / "body-filter.lua").write_text("-- stub\n", encoding="utf-8")
            for typ in ("post.typ", "page.typ", "listing.typ"):
                (root / "lib" / typ).write_text("// stub\n", encoding="utf-8")

            (root / "posts" / "2026-01-04-alpha.md").write_text(
                "---\n"
                "title: Alpha Post\n"
                "date: 2026-01-04\n"
                "updated: 2026-11-25\n"
                "description: Alpha summary.\n"
                "tags: [rust, web development]\n"
                "---\n"
                "Hello world from alpha.\n",
                encoding="utf-8",
            )
            (root / "pages" / "about.md").write_text(
                "---\ntitle: About\ndescription: About me.\n---\nHi.\n",
                encoding="utf-8",
            )
            (root / "pages" / "404.md").write_text(
                "---\ntitle: Page Not Found\ndescription: Missing.\n---\nNope.\n",
                encoding="utf-8",
            )

            pandoc_calls = 0

            def fake_run(cmd, **_kwargs):
                nonlocal pandoc_calls
                if cmd[0] == "pandoc":
                    if cmd[1] == "--version":
                        return subprocess.CompletedProcess(cmd, 0, stdout="pandoc 3.14\n", stderr="")
                    pandoc_calls += 1
                    return subprocess.CompletedProcess(cmd, 0, stdout="= Body\n", stderr="")
                if cmd[0] == "typst":
                    dst = Path(cmd[-1])
                    dst.write_text(SAMPLE_TYPST_POST_HTML, encoding="utf-8")
                    return subprocess.CompletedProcess(
                        cmd,
                        0,
                        stdout="",
                        stderr="warning: html export is under active development\n = hint: test\n",
                    )
                raise AssertionError(f"Unexpected command: {cmd}")

            with mock.patch.object(build.subprocess, "run", side_effect=fake_run):
                out_dir = build.build_site(root=root, jobs=2, clean=False)
                self.assertEqual(pandoc_calls, 3)
                # Second run should reuse cached Pandoc bodies (0 new pandoc calls)
                build.build_site(root=root, jobs=2, clean=False)
                self.assertEqual(pandoc_calls, 3)
                # --clean forces full re-conversion
                build.build_site(root=root, jobs=2, clean=True)
                self.assertEqual(pandoc_calls, 6)

            self.assertTrue((out_dir / "index.html").is_file())
            self.assertTrue((out_dir / "archive.html").is_file())
            self.assertTrue((out_dir / "about.html").is_file())
            self.assertTrue((out_dir / "404.html").is_file())
            self.assertTrue((out_dir / "posts" / "2026-01-04-alpha.html").is_file())
            self.assertTrue((out_dir / "tags" / "rust.html").is_file())
            self.assertTrue((out_dir / "tags" / "web-development.html").is_file())
            self.assertTrue((out_dir / "atom.xml").is_file())
            self.assertTrue((out_dir / "atom.xsl").is_file())
            self.assertTrue((out_dir / "sitemap.xml").is_file())
            # Fingerprinted CSS copy exists
            css_copies = list((out_dir / "css").glob("site.*.css"))
            self.assertEqual(len(css_copies), 1)
            # 404 has noindex and is absent from sitemap.xml
            self.assertIn('name="robots" content="noindex"', (out_dir / "404.html").read_text(encoding="utf-8"))
            self.assertNotIn("404.html", (out_dir / "sitemap.xml").read_text(encoding="utf-8"))
            # No leftover staging directories
            self.assertEqual(list(root.glob("_site.tmp.*")), [])

    def test_run_optimize_images_uv_and_fallback_and_cache_preservation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "scripts").mkdir()
            (root / "scripts" / "optimize-images.py").write_text("# stub\n", encoding="utf-8")
            static_dir = root / "static"
            staging_dir = root / "_site.tmp"
            cache_images = root / ".cache" / "images"
            manifest_path = root / ".cache" / "image-manifest.json"
            static_dir.mkdir()
            staging_dir.mkdir()
            cache_images.mkdir(parents=True)

            # uv path
            def fake_uv_run(cmd, **_kwargs):
                manifest_path.write_text(
                    '{"/images/demo.png": {"width": 640, "height": 480, "webp": "/images/demo.webp"}}\n',
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(cmd, 0)

            with (
                mock.patch.object(build.shutil, "which", return_value="/usr/bin/uv"),
                mock.patch.object(build.subprocess, "run", side_effect=fake_uv_run) as mrun,
            ):
                manifest = build.run_optimize_images(
                    root, 4, static_dir, staging_dir, cache_images, manifest_path
                )
                self.assertEqual(manifest["/images/demo.png"]["webp"], "/images/demo.webp")
                called_cmd = mrun.call_args.args[0]
                self.assertEqual(called_cmd[:3], ["/usr/bin/uv", "run", "--quiet"])

            # python3 + PIL fallback when uv is unavailable
            def fake_pil_fallback(cmd, **_kwargs):
                if "-c" in cmd:
                    return subprocess.CompletedProcess(cmd, 0)
                manifest_path.write_text('{"/pp.jpg": {"width": 200, "height": 200}}\n', encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0)

            with (
                mock.patch.object(build.shutil, "which", return_value=None),
                mock.patch.object(build.subprocess, "run", side_effect=fake_pil_fallback),
            ):
                manifest = build.run_optimize_images(
                    root, 2, static_dir, staging_dir, cache_images, manifest_path
                )
                self.assertEqual(manifest["/pp.jpg"]["width"], 200)

            # Clear error when neither uv nor PIL is available
            with (
                mock.patch.object(build.shutil, "which", return_value=None),
                mock.patch.object(
                    build.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 1),
                ),
            ):
                with self.assertRaises(build.BuildError) as ctx:
                    build.run_optimize_images(
                        root, 2, static_dir, staging_dir, cache_images, manifest_path
                    )
                self.assertIn("requires uv", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
