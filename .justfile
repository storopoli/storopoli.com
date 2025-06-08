alias b := build
alias i := install
alias c := clean
alias p := preview

# List all the available commands
default:
  just --list

# Install the site
install:
  @stack install

# Build the site
[working-directory: 'blog']
build:
  @stack exec site build

# Clean the site
[working-directory: 'blog']
clean: 
  @stack exec site build

# Preview the site
[working-directory: 'blog']
preview: install
  @stack exec site watch
