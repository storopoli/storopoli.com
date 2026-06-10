# storopoli.com

![CC-BI-NC-SA 4.0][cc-by-nc-sa-shield]

This is my personal site at [storopoli.com](https://storopoli.com).

It is a barebones static site: no site generator, no JavaScript[^javascript].
Posts are written in Markdown with [Typst](https://typst.app) math syntax,
rendered to HTML by Typst's HTML export
(via the [cmarker](https://typst.app/universe/package/cmarker) package),
and orchestrated by a single shell script.
Styling is the original [Tufte CSS](https://edwardtufte.github.io/tufte-css/),
in honor of the great statistician and visual displayer of information
[Edward Tufte](https://www.edwardtufte.com),
with a small override layer that adds the site chrome
and automatic light/dark mode.

## Building

Dependencies (all on Homebrew):

```sh
brew install typst just jq
# optional, for `just serve` and `just watch`:
brew install caddy watchexec
```

> [!IMPORTANT]
> Typst's HTML export is still unstable across versions.
> The site is developed and CI-pinned against **Typst 0.14.2**.
> The [cmarker](https://typst.app/universe/package/cmarker) package (pinned
> in `lib/template.typ`) is downloaded automatically on first build.

Then:

```sh
just build  # build the site into _site/
just serve  # serve _site/ on http://localhost:8080
just watch  # rebuild on change (pair with `just serve` in another pane)
just check  # build + sanity checks (links, atom.xml, no base64 images)
just new my-post-slug  # scaffold a new post
```

## Layout

- `posts/*.md` — blog posts (`YYYY-MM-DD-slug.md`, YAML frontmatter,
  Typst math inside `$...$` / `$$...$$`)
- `pages/*.md` — standalone pages (about, contact, 404)
- `lib/*.typ` — the Typst templates (site chrome, post/page/listing wrappers)
- `bib/` — BibTeX bibliography + CSL style
- `static/` — copied verbatim into `_site/` (CSS, fonts, images, CNAME, …)
- `themes/` — Gruvbox tmTheme for code highlighting
- `scripts/build.sh` — the whole build: compiles posts and pages, generates
  index/archive/tag listings and `atom.xml`

## Math Support

Anything between `$` and `$$` is [Typst math
syntax](https://typst.app/docs/reference/math/), typeset at build time and
embedded as inline SVG that follows the text color in both light and dark
mode.
No KaTeX, no MathJax, no client-side rendering.
Hooray!

## Citations

Citations are done using [BibTeX](https://www.bibtex.org/), handled by
Typst's native bibliography support with a CSL style.
Just update the [`bib/bibliography.bib`](bib/bibliography.bib) file,
set `bib: true` in the post's front matter,
and reference entries in posts:

```md
This is a valid claim [@referenceYYYY].
```

## Table of Contents

Posts automatically generate a table of contents from their headers.
You can control this behavior using metadata in your post's front matter:

```yaml
---
title: "My Post"
# Disable ToC for this post
no-toc: true
# Set ToC depth (default: 3 levels)
toc-depth: 2
# Add a Bibliography section (also appears in the ToC)
bib: true
---
```

## Syntax Highlighting

Code blocks are highlighted by Typst with a
[Gruvbox](https://github.com/morhetz/gruvbox) dark theme on a fixed dark
background in both color schemes.
I am a Gruvbox maximalist and use it for everything for years.

## License

The code is [MIT](https://mit-license.org/)
and the content is [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

[^javascript]:
    JavaScript is a security issue.
    JavaScript enables **remote code execution**.
    The browser is millions of lines of code, nobody truly knows what is going on,
    and often has escalated privileges in your computer.
    The only exception here are the YouTube embeds, which run inside
    sandboxed iframes on the privacy-enhanced `youtube-nocookie.com` host.
