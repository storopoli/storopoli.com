# storopoli.com

![CC-BI-NC-SA 4.0][cc-by-nc-sa-shield]

This is my personal site at [storopoli.com](https://storopoli.com).

It is built with [Rust](https://www.rust-lang.org/),
[Zola](https://www.getzola.org/),
and the [tabi](https://welpo.github.io/tabi) theme.

To run the site locally, you need to have Zola installed,
and run the following command;

```sh
zola serve
```

## JavaScript

By default, all JavaScript[^javascript] is disabled.

## Math Support

Math support can be enabled by setting the frontmatter with:

```toml
[extra]
katex = true
```

This will load [KaTeX](https://katex.org/)
under the hood, and anything between `$` and `$$`
will be rendered as inline or equation math
using JavaScript.

Check all the supported functions in [KaTeX documentation](https://katex.org/docs/supported).

## Mermaid

Mermaid diagrams can be enabled by setting the frontmatter with:

```toml
[extra]
mermaid = true
```

This will load [Mermaid](https://mermaid.js.org/)
under the hood, and anything between `{% mermaid() %}` and `{% end %}`
will be rendered as a Mermaid diagram.

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
