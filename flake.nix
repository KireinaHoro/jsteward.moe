{
  description = "jsteward.moe";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = inputs@{ self, nixpkgs, flake-utils }:
  with flake-utils.lib; eachSystem (defaultSystems ++ ["aarch64-darwin"]) (system: let
    pkgs = import nixpkgs { inherit system; overlays = [ self.overlay ]; };
  in rec {
    defaultPackage = pkgs.jstewardMoe;
    checks = { site = pkgs.jstewardMoe; };
  }) // {
    overlay = final: prev: {
      jstewardMoe = with final; stdenv.mkDerivation {
        name = "jsteward.moe";
        src = lib.cleanSource ./.;
        buildInputs = [
          python3Packages.pelican
          prev.python3Packages.markdown
        ];
        buildPhase = ''
          ${gnumake}/bin/make publish COMMIT=${if self ? rev then self.rev else "dirty"}
        '';
        installPhase = ''
          mkdir -p $out
          mv output/* $out/
        '';
      };
    };
  };
}
