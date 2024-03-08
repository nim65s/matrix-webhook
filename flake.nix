{
  description = "Post a message to a matrix room with a simple HTTP POST";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        matrix-webhook =
          with pkgs.python3Packages;
          buildPythonApplication {
            pname = "matrix-webhook";
            version = "3.8.0";
            src = pkgs.nix-gitignore.gitignoreSource [ ./.nixignore ] ./.;
            pyproject = true;
            buildInputs = [ poetry-core ];
            propagatedBuildInputs = [
              markdown
              matrix-nio
            ];
          };
      in
      {
        packages.default = matrix-webhook;
        apps.default = flake-utils.lib.mkApp { drv = matrix-webhook; };
        devShells.default = pkgs.mkShell {
          inputsFrom = [ matrix-webhook ];
          packages = with pkgs; [
            poetry
            python3Packages.coverage
            python3Packages.httpx
            python3Packages.safety
          ];
        };
      }
    );
}
