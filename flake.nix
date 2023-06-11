{
  description = "jsteward.moe";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils = { url = "github:numtide/flake-utils"; inputs.nixpkgs.follows = "nixpkgs"; };
  };
  outputs = inputs@{ self, nixpkgs, flake-utils }:
  with flake-utils.lib; eachSystem (defaultSystems ++ ["aarch64-darwin"]) (system: let
    pkgs = import nixpkgs { inherit system; overlays = [ self.overlay ]; };
  in rec {
    defaultPackage = pkgs.jstewardMoe;
    checks = { site = pkgs.jstewardMoe; };
  }) // {
    overlay = final: prev: {
      /*
      python = prev.python.override {
        packageOverrides = self: super: {
          pelican = super.pelican.overrideAttrs (oldAttrs: rec {
            patches = prev.writeText "jinja2-markupsafe.patch" ''
              --- source/pelican/utils.py     2021-08-01 18:33:58.588682264 +0800
              +++ source-new/pelican/utils.py 2021-08-01 18:33:43.398933115 +0800
              @@ -18,7 +18,7 @@

               import dateutil.parser

              -from jinja2 import Markup
              +from markupsafe import Markup

               import pytz

              diff -Naur source/pelican/writers.py source-new/pelican/writers.py
              --- source/pelican/writers.py   2021-08-01 18:34:10.770481673 +0800
              +++ source-new/pelican/writers.py       2021-08-01 18:33:43.398933115 +0800
              @@ -5,7 +5,7 @@

               from feedgenerator import Atom1Feed, Rss201rev2Feed, get_tag_uri

              -from jinja2 import Markup
              +from markupsafe import Markup

               from pelican.paginator import Paginator
               from pelican.plugins import signals

            '';
          });
        };
      }; */
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
