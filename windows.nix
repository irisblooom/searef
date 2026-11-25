{ pkgs }:

import ~/proj/master_window/templates/webapp_template/windows.nix {
  inherit pkgs;
  profileName = "searef/firefox";
  appId = "searef-firefox";
  startUrl = "https://github.com";
  launcherName = "searef-firefox";
}
