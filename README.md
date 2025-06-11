# storopoli.com

![CC-BI-NC-SA 4.0][cc-by-nc-sa-shield]

This is my personal site at [storopoli.com](https://storopoli.com).

It is built with [Haskell](https://www.haskell.org/),
[Hakyll](https://jaspervdj.be/hakyll/),
and the [TufteCSS](https://edwardtufte.github.io/tufte-css/) theme,
in honor of the great statistician and visual displayer of information
[Edward Tufte](https://www.edwardtufte.com).

My whole setup is [Nix](https://nixos.org/)-based.
So you just need to install [Nix](https://nixos.org/download.html)
and run the following command:

```sh
nix develop . --command just build
```

## JavaScript

By default, all JavaScript[^javascript] is disabled
and I will die on this hill.

## Syntax Highlighting

Syntax highlighting is done by [Pandoc](https://pandoc.org/)
and automatically switches between light and dark themes.
I am a [Gruvbox](https://github.com/morhetz/gruvbox) maximalist
and use it for everything for years.

## Citations

Citations are done using [BibTeX](https://www.bibtex.org/)
which is handled by [Pandoc](https://pandoc.org/)
under the hood.
Just update the [`blog/bib/bibliography.bib`] file
and reference them in posts using the Pandoc citation syntax:

```md
This is a valid claim [@referenceYYYY].
```

I was heavily inspired by [Tony Zorman's BibTeX integration](https://tony-zorman.com/posts/hakyll-and-bibtex.html).

## Math Support

Math support is all rendered during static site compilation
by [KaTeX](https://katex.org/)
under the hood, and anything between `$` and `$$`
will be rendered as inline or equation math
with no JavaScript.
Hooray!
Again [Tony Zorman's KaTeX integration](https://tony-zorman.com/posts/katex-with-hakyll.html)
for the rescue.

Check all the supported functions in [KaTeX documentation](https://katex.org/docs/supported).

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
