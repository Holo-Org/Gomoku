{
  description = "Gomoku AI - A Minimax-based Gomoku bot for liskvork/Piskvork";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    git-hooks = {
      url = "github:cachix/git-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    git-hooks,
  }: let
    inherit (nixpkgs) lib;

    supportedSystems = ["x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin"];
    eachSystem = f: lib.genAttrs supportedSystems (system: f nixpkgs.legacyPackages.${system});
  in {
    checks = eachSystem (pkgs: {
      pre-commit-check = git-hooks.lib.${pkgs.system}.run {
        src = ./.;
        hooks = {
          # Python formatting
          ruff-format = {
            enable = true;
            name = "ruff-format";
            entry = "${lib.getExe pkgs.ruff} format --check";
            files = "\\.py$";
            types = ["python"];
            excludes = ["scripts/"];
          };

          # Python linting
          ruff = {
            enable = true;
            name = "ruff";
            entry = "${lib.getExe pkgs.ruff} check";
            files = "\\.py$";
            types = ["python"];
            excludes = ["scripts/"];
          };

          # Python type checking
          mypy = {
            enable = true;
            name = "mypy";
            entry = "${pkgs.python311Packages.mypy}/bin/mypy --strict --ignore-missing-imports";
            files = "\\.py$";
            types = ["python"];
            excludes = ["scripts/"];
          };

          # Commit message convention
          commit-msg = {
            enable = true;
            name = "commit-msg";
            stages = ["commit-msg"];
            entry = "${pkgs.python311.interpreter} ${./scripts/check-commit-msg.py}";
          };

          # Reject temporary commits on push
          no-fixup-push = {
            enable = true;
            name = "no-fixup-push";
            stages = ["pre-push"];
            entry = "${./scripts/check-no-fixup.sh}";
            language = "script";
          };
        };
      };
    });

    formatter = eachSystem (pkgs: pkgs.ruff);

    packages = eachSystem (pkgs: {
      default = pkgs.stdenv.mkDerivation {
        pname = "pbrain-gomoku-ai";
        version = "1.0.0";

        src = ./.;

        buildInputs = [pkgs.python311];

        installPhase = ''
          mkdir -p $out/bin
          cp -r src $out/bin/
          cp pbrain-gomoku-ai $out/bin/
          chmod +x $out/bin/pbrain-gomoku-ai
        '';

        meta = with pkgs.lib; {
          description = "Gomoku AI brain using Minimax with alpha-beta pruning";
          license = licenses.mit;
          platforms = platforms.all;
        };
      };
    });

    apps = eachSystem (pkgs: {
      default = {
        type = "app";
        program = "${self.packages.${pkgs.system}.default}/bin/pbrain-gomoku-ai";
      };
    });

    devShells = eachSystem (pkgs: {
      default = pkgs.mkShell {
        inherit (self.checks.${pkgs.system}.pre-commit-check) shellHook;

        packages =
          [
            pkgs.python311
            pkgs.ruff
            pkgs.python311Packages.mypy
          ]
          ++ self.checks.${pkgs.system}.pre-commit-check.enabledPackages;
      };
    });
  };
}
