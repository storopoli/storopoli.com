<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:atom="http://www.w3.org/2005/Atom"
  exclude-result-prefixes="atom"
>
  <xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/atom:feed">
    <html lang="en">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title><xsl:value-of select="atom:title"/> — Atom Feed</title>
        <link rel="icon" type="image/svg+xml" href="/favicon.svg"/>
        <style>
          :root {
            color-scheme: light dark;
            --paper: light-dark(#fffcf0, #100f0f);
            --ink: light-dark(#100f0f, #cecdc3);
            --ink-2: light-dark(#6f6e69, #878580);
            --ink-3: light-dark(#b7b5ac, #575653);
            --line: light-dark(#e6e4d9, #282726);
            --wash: light-dark(#f2f0e5, #1c1b1a);
            --accent: light-dark(#bc5215, #da702c);
            --serif: "Newsreader", "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
            --mono: ui-monospace, "SF Mono", "Cascadia Code", "JetBrains Mono", Menlo, Consolas, monospace;
          }
          * { box-sizing: border-box; }
          body {
            max-width: 46rem;
            margin: 0 auto;
            padding: 1.5rem clamp(1.25rem, 4vw, 2rem) 3.5rem;
            background: var(--paper);
            color: var(--ink);
            font-family: var(--serif);
            font-size: 1.15rem;
            line-height: 1.6;
          }
          header {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: baseline;
            gap: 0.5rem 1.2rem;
            padding-bottom: 0.9rem;
            border-bottom: 1px solid var(--line);
            margin-bottom: 1.8rem;
          }
          header a.site-link {
            font-style: italic;
            font-size: 1.15rem;
            font-weight: 540;
            color: inherit;
            text-decoration: none;
          }
          header a.site-link:hover { color: var(--accent); }
          header .feed-badge {
            font-family: var(--mono);
            font-size: 0.76rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--accent);
          }
          .banner {
            background: var(--wash);
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: 1rem 1.2rem;
            margin-bottom: 2.2rem;
            font-size: 0.98rem;
          }
          .banner p { margin: 0.35rem 0; }
          .banner code {
            font-family: var(--mono);
            font-size: 0.85em;
            color: var(--accent);
          }
          h1 {
            font-size: clamp(1.6rem, 1.2rem + 1.5vw, 2.2rem);
            font-weight: 540;
            margin: 0 0 0.4rem;
            line-height: 1.2;
          }
          .subtitle {
            font-family: var(--mono);
            font-size: 0.78rem;
            color: var(--ink-2);
            margin: 0 0 2rem;
          }
          .entries {
            list-style: none;
            padding: 0;
            margin: 0;
          }
          .entry {
            padding: 1.1rem 0;
            border-bottom: 1px solid var(--line);
          }
          .entry:first-child { border-top: 1px solid var(--line); }
          .entry-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.3rem 0.9rem;
            font-family: var(--mono);
            font-size: 0.76rem;
            color: var(--ink-2);
            margin-bottom: 0.3rem;
          }
          .entry-tags {
            display: inline-flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            color: var(--accent);
          }
          .entry-title {
            margin: 0 0 0.35rem;
            font-size: 1.22rem;
            font-weight: 540;
            line-height: 1.3;
          }
          .entry-title a {
            color: inherit;
            text-decoration: none;
          }
          .entry-title a:hover { color: var(--accent); }
          .entry-summary {
            margin: 0;
            color: var(--ink-2);
            font-size: 1rem;
          }
          footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid var(--line);
            font-family: var(--mono);
            font-size: 0.74rem;
            color: var(--ink-2);
          }
          footer a { color: inherit; text-decoration: none; }
          footer a:hover { color: var(--accent); }
        </style>
      </head>
      <body>
        <header>
          <a class="site-link" href="/">
            <xsl:value-of select="atom:title"/>
          </a>
          <span class="feed-badge">Atom Feed</span>
        </header>

        <main>
          <div class="banner">
            <p>
              <strong>This is an Atom web feed.</strong>
              Subscribe by copying this page's URL into your feed reader:
              <code><xsl:value-of select="atom:id"/></code>
            </p>
            <p>
              Every entry includes the full post body (with math, syntax highlighting, and footnotes).
            </p>
          </div>

          <h1>Recent Posts</h1>
          <p class="subtitle">
            <xsl:value-of select="count(atom:entry)"/>
            <xsl:text> entries · last updated </xsl:text>
            <xsl:value-of select="substring(atom:updated, 1, 10)"/>
          </p>

          <ul class="entries">
            <xsl:for-each select="atom:entry">
              <li class="entry">
                <div class="entry-meta">
                  <time>
                    <xsl:value-of select="substring(atom:published, 1, 10)"/>
                  </time>
                  <xsl:if test="substring(atom:updated, 1, 10) != substring(atom:published, 1, 10)">
                    <span>
                      <xsl:text>updated </xsl:text>
                      <xsl:value-of select="substring(atom:updated, 1, 10)"/>
                    </span>
                  </xsl:if>
                  <xsl:if test="atom:category">
                    <span class="entry-tags">
                      <xsl:for-each select="atom:category">
                        <span>
                          <xsl:text>#</xsl:text>
                          <xsl:value-of select="@term"/>
                        </span>
                      </xsl:for-each>
                    </span>
                  </xsl:if>
                </div>
                <h2 class="entry-title">
                  <a>
                    <xsl:attribute name="href">
                      <xsl:value-of select="atom:link/@href"/>
                    </xsl:attribute>
                    <xsl:value-of select="atom:title"/>
                  </a>
                </h2>
                <p class="entry-summary">
                  <xsl:value-of select="atom:summary"/>
                </p>
              </li>
            </xsl:for-each>
          </ul>
        </main>

        <footer>
          <a href="/">← Back to site</a>
          <xsl:text> · </xsl:text>
          <a href="/archive.html">archive</a>
        </footer>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
