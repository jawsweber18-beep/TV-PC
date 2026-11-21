#!/bin/bash
# Install the TV menu from this repository into the current user's home folder.
set -e
src="https://raw.githubusercontent.com/jawsweber18-beep/TV-PC/main/tv-menu"
mkdir -p ~/.local/share/tv-menu ~/.local/bin ~/.config/autostart ~/.local/share/applications
curl -fsSL "$src/server.py"  -o ~/.local/share/tv-menu/server.py
curl -fsSL "$src/index.html" -o ~/.local/share/tv-menu/index.html
curl -fsSL "$src/tv-menu"    -o ~/.local/bin/tv-menu
chmod +x ~/.local/bin/tv-menu
cat > ~/.local/share/applications/tv-menu.desktop <<DESKTOP
[Desktop Entry]
Type=Application
Name=TV Menu
Icon=video-television
Exec=$HOME/.local/bin/tv-menu
DESKTOP
cp ~/.local/share/applications/tv-menu.desktop ~/.config/autostart/

# Keep the menu's server running in the background so the menu opens quickly.
# KillMode=process lets games and apps keep running when the server restarts.
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/tv-menu.service <<'UNIT'
[Unit]
Description=TV menu server

[Service]
ExecStart=/usr/bin/python3 %h/.local/share/tv-menu/server.py
Restart=on-failure
KillMode=process

[Install]
WantedBy=default.target
UNIT
pkill -f 'tv-menu/server.py' || true
if ! { systemctl --user daemon-reload && systemctl --user enable tv-menu.service \
       && systemctl --user restart tv-menu.service; }; then
  echo "Note: couldn't set up the background service; the menu will start its server when opened."
fi
echo "TV menu installed. Open it from the start menu (TV Menu) or reboot."
