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

# Serve _site/ locally
serve:
  python3 -m http.server 8080 -d _site

# Rebuild on change (brew install watchexec); run `just serve` in another pane
watch:
  watchexec --exts md,typ,css,bib,sh,py,lua -- just build

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
  @python3 -c "import xml.etree.ElementTree as ET; ET.parse('_site/atom.xml')"
  @echo "==> Shell scripts pass shellcheck"
  @if command -v shellcheck >/dev/null 2>&1; then \
    shellcheck scripts/*.sh; \
  else \
    echo "(shellcheck not installed, skipping)"; \
  fi
  @echo "==> Internal links resolve"
  @if command -v lychee >/dev/null 2>&1; then \
    lychee --offline --root-dir "$(pwd)/_site" "_site"; \
  else \
    echo "(lychee not installed, skipping)"; \
  fi
  @echo "OK"
