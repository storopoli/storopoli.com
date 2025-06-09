{
  description = "storopoli.com Hakyll flake";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Build the Haskell site generator executable from the blog subdirectory
        siteBuilder = hPkgs.callCabal2nix "blog" ./blog {
          # Add any Haskell dependencies here if needed
        };

        # need to match Stackage LTS version from stack.yaml snapshot
        hPkgs = pkgs.haskell.packages."ghc984";

        myDevTools = [
          hPkgs.ghc # GHC compiler in the desired version (will be available on PATH)
          hPkgs.ghcid # Continuous terminal Haskell compile checker
          hPkgs.ormolu # Haskell formatter
          hPkgs.hlint # Haskell codestyle checker
          hPkgs.hoogle # Lookup Haskell documentation
          hPkgs.haskell-language-server # LSP server for editor
          hPkgs.implicit-hie # auto generate LSP hie.yaml file from cabal
          hPkgs.retrie # Haskell refactoring tool
          hPkgs.cabal-install
          stack-wrapped
          pkgs.zlib # External C library needed by some Haskell packages
          pkgs.just
          pkgs.deno # KaTeX rendering of maths—see blog/scripts/math.ts
          pkgs.pandoc
        ];

        haskellDeps = with hPkgs; [
          hakyll
          pandoc
          pandoc-types
          pandoc-sidenote
          text
          process
        ];

        # Wrap Stack to work with our Nix integration. We don't want to modify
        # stack.yaml so non-Nix users don't notice anything.
        # - no-nix: We don't want Stack's way of integrating Nix.
        # --system-ghc    # Use the existing GHC on PATH (will come from this Nix file)
        # --no-install-ghc  # Don't try to install GHC if no matching GHC found on PATH
        stack-wrapped = pkgs.symlinkJoin {
          name = "stack"; # will be available as the usual `stack` in terminal
          paths = [ pkgs.stack ];
          buildInputs = [ pkgs.makeWrapper ];
          postBuild = ''
            wrapProgram $out/bin/stack \
              --add-flags "\
                --no-nix \
                --system-ghc \
                --no-install-ghc \
              "
          '';
        };
      in {
        packages.default = pkgs.stdenv.mkDerivation {
          name = "website";
          buildInputs = [ siteBuilder ];
          src = pkgs.nix-gitignore.gitignoreSourcePure [
            ./.gitignore
            ".git"
            ".github"
          ] ./.;

          LANG = "en_US.UTF-8";
          LOCALE_ARCHIVE =
            pkgs.lib.optionalString (pkgs.buildPlatform.libc == "glibc")
            "${pkgs.glibcLocales}/lib/locale/locale-archive";

          buildPhase = ''
            # Copy the ssg directory to root for build context
            cp -r blog/* .

            # Run the site generator to build the website
            ${siteBuilder}/bin/site build
          '';

          installPhase = ''
            mkdir -p "$out"
            cp -r _site/. "$out/"
          '';
        };

        devShells.default = pkgs.mkShell {
          buildInputs = myDevTools ++ haskellDeps;

          # Make external Nix c libraries like zlib known to GHC, like
          # pkgs.haskell.lib.buildStackProject does
          # https://github.com/NixOS/nixpkgs/blob/d64780ea0e22b5f61cd6012a456869c702a72f20/pkgs/development/haskell-modules/generic-stack-builder.nix#L38
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath myDevTools;
        };
      });
}
