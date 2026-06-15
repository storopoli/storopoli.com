# storopoli.com

![CC-BI-NC-SA 4.0][cc-by-nc-sa-shield]

This is my personal site at [storopoli.com](https://storopoli.com).

It is a barebones static site: no site generator, no JavaScript[^javascript].
Posts are written in Markdown with [Typst](https://typst.app) math syntax;
[Pandoc](https://pandoc.org) converts the Markdown to Typst markup (passing
the math through verbatim via a small Lua filter), Typst's HTML export
renders the pages, and a single shell script orchestrates everything.

Styling is a single hand-written stylesheet (`static/css/site.css`) around
one idea: _literary text, terminal chrome_. Prose is set in
[Newsreader](https://github.com/productiontype/Newsreader), a contemporary
editorial serif (self-hosted variable woff2 with optical sizing); everything
machine-adjacent — nav, dates, tags, labels, captions, footnote markers,
code — is monospaced. One color system throughout, after
[Flexoki](https://stephango.com/flexoki): warm paper/ink surfaces in both
color schemes, one burnt-orange accent, the Flexoki accents for syntax
highlighting, and automatic light/dark mode.

## Building

Dependencies (all on Homebrew):

```sh
brew install typst pandoc just jq
# optional, for `just watch`:
brew install watchexec
```

> [!IMPORTANT]
> Typst's HTML export is still unstable across versions.
> The site is developed and CI-pinned against **Typst 0.15.0**
> and **Pandoc 3.9**.

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
- `bib/` — BibTeX bibliography (rendered with Typst's built-in IEEE style)
- `static/` — copied verbatim into `_site/` (CSS, fonts, images, CNAME, …);
  `static/fonts/` holds the self-hosted Newsreader variable woff2 files
  (latin + latin-ext, normal + italic, pinned from
  [fontsource](https://fontsource.org/fonts/newsreader) 5.2.10)
- `scripts/build.sh` — the whole build: converts Markdown with Pandoc,
  compiles posts and pages with Typst, generates index/archive/tag
  listings and `atom.xml`
- `scripts/body-filter.lua` — the Pandoc filter: Typst math passthrough,
  image figures, YouTube embeds

## Math Support

Anything between `$` and `$$` is [Typst math
syntax](https://typst.app/docs/reference/math/), typeset at build time and
exported as native [MathML](https://developer.mozilla.org/en-US/docs/Web/MathML).
It is accessible to screen readers, selectable and copyable, scales with zoom
and font size, and follows the text color in both light and dark mode.
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

Posts automatically generate a table of contents from their headers,
rendered as a native `<details>` element (collapsed by default, no
JavaScript).
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

Code blocks are highlighted by Typst's built-in default raw theme, which
only classifies the tokens: `scripts/postprocess.py` rewrites its colors
into role classes (`.tok-red`, `.tok-green`, …) that `site.css` renders in
the [Flexoki](https://stephango.com/flexoki) accents — 600-series in light
mode, 400-series in dark mode — so code shares one color system with the
rest of the site. If a Typst upgrade ever changes the default theme's
palette, postprocess fails the build listing the unmapped colors.

## Light/Dark Mode

The site follows the system color scheme, and the `◐` button in the header
flips it — pure CSS (`light-dark()` + a checkbox), no JavaScript, so the
choice resets on navigation.

## License

The code is [MIT](https://mit-license.org/)
and the content is [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

[^javascript]: JavaScript is a security issue.
    JavaScript enables **remote code execution**.
    The browser is millions of lines of code, nobody truly knows what is going on,
    and often has escalated privileges in your computer.
    The only exception here are the YouTube embeds, which run inside
    sandboxed iframes on the privacy-enhanced `youtube-nocookie.com` host.
