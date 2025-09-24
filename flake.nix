{
  description = "storopoli.com Hakyll flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
    git-hooks.url = "github:cachix/git-hooks.nix";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      git-hooks,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        lib = "blog";

        pkgs = import nixpkgs {
          inherit system;
          config.allowBroken = true;
        };

        hlib = pkgs.haskell.lib;

        # ghc 9.8.4 is 25.05
        hpkgs = pkgs.haskell.packages.ghc984.extend (
          new: old: {
            ${lib} = new.callCabal2nix lib ./blog { };
            # tests are broken somehow in these deps
            pandoc-sidenote = hlib.dontCheck old.pandoc-sidenote;
          }
        );

        inherit (pkgs.stdenv) cc;
        inherit (hpkgs) ghc;
        cabal = hpkgs.cabal-install;

        # Shared source for both derivations
        src =
          pkgs.nix-gitignore.gitignoreSourcePure
            [
              ./.gitignore
              ".git"
              ".github"
            ]
            (
              builtins.path {
                path = ./.;
                name = "source";
              }
            );

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

        website = pkgs.stdenv.mkDerivation {
          name = "website";
          buildInputs = with pkgs; [
            hpkgs.${lib}
            deno
          ];
          inherit src;

          LANG = "en_US.UTF-8";
          LOCALE_ARCHIVE = pkgs.lib.optionalString (
            pkgs.buildPlatform.libc == "glibc"
          ) "${pkgs.glibcLocales}/lib/locale/locale-archive";
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
            ${hpkgs.${lib}}/bin/site build --verbose
          '';

          installPhase = ''
            mkdir -p "$out"
            cp -a _site/. "$out/"
          '';
        };
      in
      {

        packages = {
          inherit website vendorDir;
          default = website;
        };

        apps.default = flake-utils.lib.mkApp {
          drv = hpkgs.${lib};
          exePath = "/bin/site";
        };

        devShells.default = hpkgs.shellFor {
          packages = p: [
            (hlib.doBenchmark p.${lib})
          ];

          buildInputs = with pkgs; [
            cabal
            cc
            hpkgs.haskell-language-server
            hpkgs.fourmolu
            hpkgs.cabal-fmt
            hpkgs.hlint
            just
            deno
            typos
            nil
            nixfmt-rfc-style
            statix
          ];

          inputsFrom = builtins.attrValues self.packages.${system};

          doBenchmark = true;

          shellHook = ''
            PS1="[${lib}] \w$ "
            echo "entering ${system} shell, using"
            echo "cc:    $(${cc}/bin/cc --version)"
            echo "ghc:   $(${ghc}/bin/ghc --version)"
            echo "cabal: $(${cabal}/bin/cabal --version)"
          '';
        };

        checks.git-hooks-check = git-hooks.lib.${system}.run {
          src = ./.;
          hooks = {
            # Nix
            nixfmt-rfc-style.enable = true;
            statix.enable = true;
            flake-checker = {
              enable = true;
              args = [
                "--check-outdated"
                "false" # don't check for nixpkgs
              ];
            };

            # Haskell
            cabal2nix.enable = true;
            fourmolu.enable = true;
            cabal-fmt.enable = true;
            hlint.enable = true;

            # Tin-foil hat
            zizmor.enable = true;
          };
        };

      }
    );
}
