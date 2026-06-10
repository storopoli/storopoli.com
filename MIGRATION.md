# Migration checklist (Hakyll → typst)

Temporary tracking file — delete when the migration is complete.

Per-post procedure:

1. `git mv blog/posts/X.md posts/X.md`
2. Convert math inside `$...$` / `$$...$$` from LaTeX to typst syntax
   (`\frac{a}{b}` → `a/b`, `\begin{aligned}` → `&` alignment, `\begin{cases}` →
   `cases(...)`, `\mathbb{N}` → `NN`, `\to` → `->`, custom macros expanded)
3. Remove `{-}` marginnote markers in footnote definitions
4. Normalize bare `@key` citations to `[@key]`
5. Escape literal `$` in prose as `\$`
6. `just build` must pass (zero non-banner warnings)
7. Browser check: light + dark scheme, 375px mobile, math, code, footnotes,
   images, embeds, ToC anchors
8. Tick the row, commit `feat(posts): migrate <slug> math to typst`

## Posts

| Post | Migrated | Verified light | Verified dark | Notes |
| --- | --- | --- | --- | --- |
| 2023-11-10-soydev | x | x | x | pilot |
| 2023-11-20-word_embeddings | x | x | x | pilot |
| 2023-11-23-lindley_paradox | x | x | x | pilot, bib + aligned |
| 2023-11-28-zero_cost_abstractions | | | | |
| 2024-01-14-htmx | | | | |
| 2024-01-30-sudoku | | | | raw HTML form elements |
| 2024-02-05-crypto-basics | | | | 261 inline + 32 display eqs |
| 2024-02-11-mnemonic | | | | |
| 2024-03-23-dead-man-switch | x | x | x | pilot, marginnote |
| 2024-04-14-shamir-secret-sharing | | | | |
| 2024-06-08-zkp | | | | bib |
| 2024-06-22-von-neumann | | | | YouTube embed |
| 2024-11-03-zig-comptime | | | | YouTube embed |
| 2024-11-10-road-less-travelled | | | | YouTube embed |
| 2024-11-15-taproot | | | | bib |
| 2025-02-10-bitvm | | | | bib + embed |
| 2025-04-07-randomness | | | | bib |
| 2025-05-24-beauty-of-math-incompleteness | | | | cases + tables + embed |
| 2025-07-24-dev-workflow | | | | YouTube embed |
| 2025-08-09-letter-to-my-son | | | | no-toc |
| 2025-11-09-bifi | | | | no-toc |
| 2026-01-04-evm-yubikeys | | | | |

## Pages

| Page | Migrated | Verified |
| --- | --- | --- |
| about | x | x |
| contact | x | x |
| 404 | x | x |
