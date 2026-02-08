alias b := build
alias i := install
alias c := clean
alias p := preview

# List all the available commands
default:
  just --list

# Install the site 
install:
  @if command -v nix >/dev/null 2>&1; then \
    nix build; \
  else \
    cabal build exe:site; \
  fi

# Ensure we can render math (needed for build/preview)
require-math-runtime:
  @if command -v nix >/dev/null 2>&1 || command -v deno >/dev/null 2>&1; then \
    true; \
  else \
    echo "Error: build/preview requires either 'nix' or 'deno' in PATH." >&2; \
    echo "Install Nix, or install Deno to use the non-Nix fallback." >&2; \
    exit 1; \
  fi

# Build the site
[working-directory: 'blog']
build: require-math-runtime install deno
  @if command -v nix >/dev/null 2>&1; then \
    nix run .. -- build; \
  elif command -v deno >/dev/null 2>&1; then \
    cabal run site -- build; \
  else \
    echo "Error: building the site requires either 'nix' or 'deno' in PATH." >&2; \
    echo "Install Nix, or install Deno to use the non-Nix fallback." >&2; \
    exit 1; \
  fi

# Clean the site
[working-directory: 'blog']
clean:
  @if command -v nix >/dev/null 2>&1; then \
    nix run .. -- clean; \
  else \
    cabal run site -- clean; \
  fi
  @rm -rf vendor
  @rm -rf import_map.json
  @rm -rf _site

# Preview the site
[working-directory: 'blog']
preview: require-math-runtime install deno
  @if command -v nix >/dev/null 2>&1; then \
    nix run .. -- watch; \
  elif command -v deno >/dev/null 2>&1; then \
    cabal run site -- watch; \
  else \
    echo "Error: preview requires either 'nix' or 'deno' in PATH." >&2; \
    echo "Install Nix, or install Deno to use the non-Nix fallback." >&2; \
    exit 1; \
  fi

# Lint the site
[working-directory: 'blog']
lint:
  @hlint .

# Setup deno cache for KaTeX
deno:
  #!/usr/bin/env bash
  run_deno() {
    if command -v deno >/dev/null 2>&1; then
      deno "$@"
    elif command -v nix >/dev/null 2>&1; then
      nix develop .. --command deno "$@"
    else
      echo "Error: deno setup requires either 'deno' or 'nix' in PATH." >&2
      exit 1
    fi
  }

  # Set up deno vendor directory and import map for development
  if [ ! -d blog/vendor ]; then
    echo "Setting up deno vendor directory..."
    cd blog
    run_deno cache --vendor scripts/math.ts
    cd ..
  fi

  # Create import map if it doesn't exist
  if [ ! -f blog/import_map.json ]; then
    echo "Creating import map..."
    cat > blog/import_map.json << 'EOF'
  {
    "imports": {
      "https://deno.land/std@0.224.0/": "./vendor/deno.land/std@0.224.0/",
      "https://cdn.jsdelivr.net/npm/katex@0.16.11/": "./vendor/cdn.jsdelivr.net/npm/katex@0.16.11/"
    }
  }
  EOF
  fi
