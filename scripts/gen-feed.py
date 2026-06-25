"""Generate the Atom feed, full-content (argv: posts.json, _site dir).

The metadata-only feed (title + summary) left readers with no way to read a
post without leaving the app. This re-emits each entry with the post's whole
body in <content type="html"> so feed readers render the article inline.

The body is lifted straight from the already-built post page (so math,
syntax highlighting and footnotes come along for free), with the page chrome
that doesn't belong in a feed stripped out:

  * the <h1> title and the post-meta line (date/author/tags) — the Atom
    entry already carries all of that as real metadata;
  * the table-of-contents <details> — its in-page anchors are noise in a
    reader.

Root-relative URLs (/images/..., /posts/...) are rewritten to absolute so
images and links resolve in a reader that has no notion of the site origin;
in-page fragments (#fn1) are left alone so footnote jumps keep working
inside the rendered entry. The result is escaped into <content type="html">
rather than emitted as XHTML: typst's output has void tags (<img>, <hr>,
<input>) that aren't well-formed XML, so escaped HTML is the safe encoding.
"""

import html
import json
import re
import sys

SITE_URL = "https://storopoli.com"
SITE_TITLE = "Jose Storopoli, PhD"
AUTHOR_NAME = "Jose Storopoli, PhD"
AUTHOR_EMAIL = "jose@storopoli.com"

# The post body lives inside <main>; everything else (header/footer/nav) is
# site chrome we never want in the feed.
MAIN = re.compile(r"<main\b[^>]*>(.*?)</main>", re.S)
H1 = re.compile(r"<h1\b[^>]*>.*?</h1>", re.S)
POST_META = re.compile(r'<div class="post-meta">.*?</div>', re.S)
TOC = re.compile(r'<details\b[^>]*\bid="table-of-contents"[^>]*>.*?</details>', re.S)
# Root-relative href/src (a single leading slash, not protocol-relative "//").
ROOT_REL = re.compile(r'(\b(?:href|src)=")/(?!/)')


def post_content(site_dir, slug):
    """Article HTML for one post, chrome stripped and URLs absolutized.

    Returns None when the page is missing or has no <main> (the entry then
    falls back to summary-only, exactly as before)."""
    try:
        page = open(f"{site_dir}/posts/{slug}.html", encoding="utf-8").read()
    except OSError:
        return None
    main = MAIN.search(page)
    if not main:
        return None
    body = main.group(1)
    body = H1.sub("", body, count=1)
    body = POST_META.sub("", body, count=1)
    body = TOC.sub("", body, count=1)
    body = ROOT_REL.sub(rf"\1{SITE_URL}/", body)
    return body.strip()


def text(s):
    """Escape a string for XML element text."""
    return html.escape(s, quote=False)


def rfc(date):
    """Frontmatter date (YYYY-MM-DD) -> RFC 3339 timestamp."""
    return f"{date}T00:00:00Z"


def entry(post, site_dir):
    url = SITE_URL + post["url"]
    summary = post.get("description") or post["title"]
    out = [
        "  <entry>",
        f"    <title>{text(post['title'])}</title>",
        f'    <link href="{url}"/>',
        f"    <id>{url}</id>",
        f"    <published>{rfc(post['date'])}</published>",
        f"    <updated>{rfc(post['date'])}</updated>",
        f"    <summary>{text(summary)}</summary>",
    ]
    content = post_content(site_dir, post["slug"])
    if content:
        out.append(f'    <content type="html">{text(content)}</content>')
    out.append("  </entry>")
    return out


def main():
    posts_json, site_dir = sys.argv[1], sys.argv[2]
    posts = json.load(open(posts_json, encoding="utf-8"))
    updated = rfc(posts[0]["date"]) if posts else rfc("2000-01-01")

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"  <title>{text(SITE_TITLE)}</title>",
        f'  <link href="{SITE_URL}/atom.xml" rel="self"/>',
        f'  <link href="{SITE_URL}"/>',
        f"  <id>{SITE_URL}/atom.xml</id>",
        f"  <updated>{updated}</updated>",
        f"  <author><name>{text(AUTHOR_NAME)}</name>"
        f"<email>{AUTHOR_EMAIL}</email></author>",
    ]
    for post in posts:
        lines += entry(post, site_dir)
    lines.append("</feed>")
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
