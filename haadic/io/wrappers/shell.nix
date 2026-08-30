#!/usr/bin/env nix-shell
let
  nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-26.05";
  nixpkgs_25 = fetchTarball "https://github.com/NixOS/nixpkgs/tarball/nixos-25.11";
  pkgs = import nixpkgs { config = {}; overlays = []; };
  pkgs_25 = import nixpkgs_25 { config = {}; overlays = []; };
in

pkgs.mkShellNoCC {
  packages = [
    pkgs.ngspice
    pkgs_25.magic-vlsi
  ];

}
