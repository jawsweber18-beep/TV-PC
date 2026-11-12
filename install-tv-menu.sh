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
pkill -f 'tv-menu/server.py' || true
echo "TV menu installed. Open it from the start menu (TV Menu) or reboot."
