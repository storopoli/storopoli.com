alias b := build
alias s := serve
alias c := clean
alias w := watch

# List all the available commands
default:
  just --list

# Build the site into _site/
build:
  ./scripts/build.sh

# Serve _site/ locally (brew install caddy; falls back to python3)
serve:
  @if command -v caddy >/dev/null 2>&1; then \
    caddy file-server --root _site --listen :8080; \
  else \
    python3 -m http.server 8080 -d _site; \
  fi

# Rebuild on change (brew install watchexec); run `just serve` in another pane
watch:
  watchexec --exts md,typ,css,bib,csl,tmTheme,sh -- just build

# Remove build artifacts
clean:
  rm -rf _site .cache

# Scaffold a new post
new slug:
  ./scripts/new-post.sh {{slug}}

# Spell check
lint:
  typos

# Build and run sanity checks over the output
check: build
  @echo "==> No base64 data URIs in posts"
  @! grep -rl 'src="data:' _site/posts 2>/dev/null
  @echo "==> atom.xml is well-formed"
  @if command -v xmllint >/dev/null 2>&1; then xmllint --noout _site/atom.xml; fi
  @echo "==> Internal links resolve"
  @if command -v lychee >/dev/null 2>&1; then \
    lychee --offline --root-dir "$(pwd)/_site" "_site/**/*.html"; \
  else \
    echo "(lychee not installed, skipping)"; \
  fi
  @echo "OK"
