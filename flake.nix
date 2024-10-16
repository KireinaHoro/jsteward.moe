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
    apps.default = let
      serve = pkgs.writeShellApplication {
        # serve the built local tree on port 8080
        name = "serve";
        runtimeInputs = [pkgs.caddy];
        text = ''
          caddy file-server --listen localhost:8080 --root ${pkgs.jstewardMoe} --access-log
        '';
      };
    in {
      type = "app";
      program = "${serve}/bin/serve";
    };
  }) // {
    overlay = final: prev: {
      jstewardMoe = with final; stdenv.mkDerivation {
        name = "jsteward.moe";
        src = lib.cleanSource ./.;
        buildInputs = with python3Packages; [ pelican markdown ];
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
