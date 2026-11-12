# TV-PC

A big-icon TV menu for a Bazzite (KDE) living-room PC, controllable with a game controller, an air mouse or a keyboard.

It shows three rows of tiles:

- **Apps**: YouTube, Steam (Big Picture), Brave and a Desktop tile that closes the menu
- **Games**: every game launcher on the desktop (from `rom-desktop`), labeled with its system
- **Shortcuts**: any other launchers on the desktop

The menu opens full-screen when you log in. Move with the d-pad, left stick or arrow keys; open with A, Enter or a click.

## Install

```bash
sudo flatpak install -y flathub com.brave.Browser org.mozilla.firefox
curl -fsSL https://raw.githubusercontent.com/jawsweber18-beep/TV-PC/main/install-tv-menu.sh | bash
```

Firefox runs the menu itself; Brave is used for the Browser and YouTube tiles.

## Customize

The Apps row comes from `~/.config/tv-menu/apps.json` (created on first run). Each tile has a `name`, an optional `icon` (an icon name or file path), and either an `exec` command list or `"action": "close"`:

```json
{"name": "Kodi", "icon": "tv.kodi.Kodi", "exec": ["flatpak", "run", "tv.kodi.Kodi"]}
```

The menu reloads its tiles every 30 seconds.

## Files

| File | Installed to | Purpose |
|---|---|---|
| `tv-menu/server.py` | `~/.local/share/tv-menu/` | Local server (127.0.0.1:8765) that lists tiles and starts apps |
| `tv-menu/index.html` | `~/.local/share/tv-menu/` | The menu page |
| `tv-menu/tv-menu` | `~/.local/bin/` | Starts the server and opens the menu in a full-screen Firefox window |
