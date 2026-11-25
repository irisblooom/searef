{ pkgs ? import <nixpkgs> { } }:

let
  windows = import ./windows.nix { inherit pkgs; };
  browserWindow = builtins.elemAt windows 2;
  firefoxLauncher = builtins.elemAt browserWindow.packages 0;
  ghAuthBrowser = pkgs.writeShellApplication {
    name = "searef-gh-auth-browser";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''
      runtime_dir="''${XDG_RUNTIME_DIR:-/tmp}"
      auth_home="$(mktemp -d "$runtime_dir/searef-gh-firefox.XXXXXX")"
      export NUKED_FIREFOX_HOME="$auth_home"
      exec ${firefoxLauncher}/bin/searef-firefox "$@"
    '';
  };
in
pkgs.mkShell {
  packages = with pkgs; [
    git
    gh
    ghAuthBrowser
  ];

  # gh auth login --web uses the webapp-template Firefox configuration.
  shellHook = ''
    export BROWSER="${ghAuthBrowser}/bin/searef-gh-auth-browser"
  '';
}
