alias b := build
alias i := install
alias c := clean
alias p := preview

# List all the available commands
default:
  just --list

# Install the site 
install:
  @nix build

# Build the site
[working-directory: 'blog']
build: install deno
  @nix run . -- build

# Clean the site
[working-directory: 'blog']
clean:
  @nix run . -- clean
  @rm -rf vendor
  @rm -rf import_map.json
  @rm -rf _site

# Preview the site
[working-directory: 'blog']
preview: install deno
  @nix run . -- watch

# Lint the site
[working-directory: 'blog']
lint:
  @hlint .

# Setup deno cache for KaTeX
deno:
  #!/usr/bin/env bash
  # Set up deno vendor directory and import map for development
  if [ ! -d blog/vendor ]; then
    echo "Setting up deno vendor directory..."
    cd blog
    deno cache --vendor scripts/math.ts
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
