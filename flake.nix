{
  description = "jsteward.moe";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    resume = {
      url = "github:KireinaHoro/resume";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = inputs@{ self, nixpkgs, flake-utils, resume }:
  with flake-utils.lib; eachSystem (defaultSystems ++ ["aarch64-darwin"]) (system: let
    pkgs = import nixpkgs { inherit system; };
    cv = "${resume.packages.${system}.default}/cv.pdf";
    myPython = pkgs.python3.withPackages (ps: with ps; [
      pelican
      markdown
      pillow
    ]);
    website = pkgs.stdenvNoCC.mkDerivation {
      name = "jsteward.moe";
      src = pkgs.lib.cleanSource ./.;
      buildInputs = [ myPython ];
      buildPhase = ''
        mkdir -p $out
        python3 -m pelican
        cp ${cv} $out/images/
      '';
      COMMIT = if self ? rev then self.rev else "dirty";
    };
  in {
    checks = { inherit website; };
    apps.default = let
      serve = pkgs.writeShellApplication {
        # serve the built local tree on port 8080
        name = "serve";
        runtimeInputs = [ pkgs.caddy ];
        text = ''
          caddy file-server --listen localhost:8880 --root ${website} --access-log
        '';
      };
    in {
      type = "app";
      program = "${serve}/bin/serve";
    };
    devShells.default = pkgs.mkShell {
      buildInputs = [ myPython pkgs.getopt ]; # getopt for imaging/collage/image-export.sh
    };
    packages.default = website;
  });
}
