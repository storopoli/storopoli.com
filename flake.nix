{
  description = "storopoli.com Hakyll flake";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # need to match Stackage LTS version from stack.yaml snapshot
        hPkgs = pkgs.haskell.packages."ghc984";

        # Shared source for both derivations
        src = pkgs.nix-gitignore.gitignoreSourcePure [
          ./.gitignore
          ".git"
          ".github"
        ] (builtins.path {
          path = ./.;
          name = "source";
        });

        # Build the Haskell site generator executable from the blog subdirectory
        siteBuilder = hPkgs.callCabal2nix "blog" ./blog {
          # Add any Haskell dependencies here if needed
        };

        # Vendor deno dependencies
        vendorDir = pkgs.stdenv.mkDerivation {
          name = "deno-vendor";
          inherit src;
          nativeBuildInputs = [ pkgs.deno ];

          # Set HOME to a writable directory for deno cache
          preBuild = ''
            export HOME=$TMPDIR
          '';

          buildPhase = ''
            cd blog
            deno cache --vendor scripts/math.ts
          '';

          installPhase = ''
            mkdir -p $out
            cp -r vendor $out/
          '';

          # This makes it a fixed-output derivation, allowing network access
          outputHashMode = "recursive";
          outputHashAlgo = "sha256";
          outputHash = "sha256-sbqPST20JuaZJKX8yjfS5di5GiE+BjbEW3rEhsHY2p4=";
        };

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
          pkgs.just
          pkgs.deno # KaTeX rendering of maths—see blog/scripts/math.ts
        ];

        haskellDeps = with hPkgs; [
          pkgs.zlib # External C library needed by some Haskell packages
          hakyll
          pandoc
          pandoc-types
          pandoc-sidenote
          text
          process
          filepath
          skylighting-core
          bytestring
          pkgs.pandoc
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
        website = pkgs.stdenv.mkDerivation {
          name = "website";
          buildInputs = [ siteBuilder pkgs.deno ] ++ haskellDeps;
          inherit src;

          LANG = "en_US.UTF-8";
          LOCALE_ARCHIVE =
            pkgs.lib.optionalString (pkgs.buildPlatform.libc == "glibc")
            "${pkgs.glibcLocales}/lib/locale/locale-archive";
          buildPhase = ''
            cd blog

            # Copy vendor directory from the vendor derivation
            cp -r ${vendorDir}/vendor ./

            # Create import map for deno to use vendored dependencies
            cat > import_map.json << EOF
            {
              "imports": {
                "https://deno.land/std@0.224.0/": "./vendor/deno.land/std@0.224.0/",
                "https://cdn.jsdelivr.net/npm/katex@0.16.11/": "./vendor/cdn.jsdelivr.net/npm/katex@0.16.11/"
              }
            }
            EOF

            # Run the site generator
            ${siteBuilder}/bin/site build --verbose
          '';

          installPhase = ''
            mkdir -p "$out"
            cp -a _site/. "$out/"
          '';
        };
      in {

        packages = {
          inherit siteBuilder website vendorDir;
          default = website;
        };

        apps.default = flake-utils.lib.mkApp {
          drv = siteBuilder;
          exePath = "/bin/site";
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
