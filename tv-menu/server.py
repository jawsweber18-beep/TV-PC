#!/usr/bin/env python3
"""TV menu: serves the big-icon launcher page and starts apps when a tile is picked."""
import hashlib, json, mimetypes, os, re, secrets, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOME = Path.home()
HERE = Path(__file__).resolve().parent
CONFIG = HOME / ".config/tv-menu/apps.json"
DESKTOP = HOME / "Desktop"
PORT = int(os.environ.get("TV_MENU_PORT", "8765"))
TOKEN = secrets.token_hex(16)

# Fill in the display settings if the server was started from SSH
uid = os.getuid()
os.environ.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
os.environ.setdefault("WAYLAND_DISPLAY", "wayland-0")
os.environ.setdefault("DISPLAY", ":0")
os.environ.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path=/run/user/{uid}/bus")

DEFAULT_APPS = [
    {"name": "YouTube", "glyph": "▶", "color": "#d93025",
     "exec": ["flatpak", "run", "com.brave.Browser",
              f"--user-data-dir={HOME}/.var/app/com.brave.Browser/youtube-profile",
              "--kiosk", "https://www.youtube.com"]},
    {"name": "Steam", "icon": "steam", "exec": ["steam", "steam://open/bigpicture"]},
    {"name": "Browser", "icon": "com.brave.Browser", "exec": ["flatpak", "run", "com.brave.Browser"]},
    {"name": "Desktop", "icon": "user-desktop", "glyph": "⌂", "color": "#4f9cf9", "action": "close"},
]

ICON_DIRS = [HOME / ".local/share/icons", HOME / ".local/share/flatpak/exports/share/icons",
             Path("/var/lib/flatpak/exports/share/icons"), Path("/usr/share/icons/hicolor"),
             Path("/usr/share/icons/breeze"), Path("/usr/share/pixmaps")]
_icons = None

def icon_index():
    """Map icon names to the best file: SVG first, then the largest PNG."""
    global _icons
    if _icons is None:
        _icons, scores = {}, {}
        for base in ICON_DIRS:
            for root, _, files in os.walk(base):
                size = max([int(n) for n in re.findall(r"(\d+)x\d+", root)] or [48])
                for f in files:
                    stem, ext = os.path.splitext(f)
                    if ext not in (".svg", ".png") or stem.endswith("-symbolic"):
                        continue
                    score = 10000 if ext == ".svg" else size
                    if score > scores.get(stem, -1):
                        scores[stem], _icons[stem] = score, os.path.join(root, f)
    return _icons

def find_icon(name):
    if not name:
        return None
    if name.startswith("/"):
        return name if os.path.isfile(name) else None
    return icon_index().get(name)

def read_desktop(path):
    entry, main = {}, False
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("["):
            main = line == "[Desktop Entry]"
        elif main and "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            entry.setdefault(key.strip(), value.strip())
    return entry

def split_exec(value):
    """Turn a .desktop Exec= value into an argument list (desktop-entry quoting rules)."""
    escapes = {"s": " ", "n": "\n", "t": "\t", "r": "\r", "\\": "\\"}
    value = re.sub(r"\\(.)", lambda m: escapes.get(m.group(1), "\\" + m.group(1)), value)
    args, cur, started, quoted, i = [], "", False, False, 0
    while i < len(value):
        c = value[i]
        if quoted:
            if c == "\\" and i + 1 < len(value) and value[i + 1] in '"`$\\':
                cur += value[i + 1]
                i += 1
            elif c == '"':
                quoted = False
            else:
                cur += c
        elif c == '"':
            quoted = started = True
        elif c.isspace():
            if started:
                args.append(cur)
            cur, started = "", False
        else:
            cur += c
            started = True
        i += 1
    if started:
        args.append(cur)
    return [a.replace("%%", "%") for a in args if not re.fullmatch(r"%[fFuUdDnNickvm]", a)]

def tiles():
    if not CONFIG.exists():
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(DEFAULT_APPS, indent=2, ensure_ascii=False))
    items = [dict(app, section="Apps") for app in json.loads(CONFIG.read_text())]
    for f in sorted(DESKTOP.glob("*.desktop"), key=lambda p: p.name.lower()):
        e = read_desktop(f)
        if e.get("Type", "Application") != "Application" or "Exec" not in e or e.get("Hidden") == "true":
            continue
        items.append({"name": e.get("Name", f.stem), "sub": e.get("Comment", ""), "icon": e.get("Icon"),
                      "exec": split_exec(e["Exec"]),
                      "section": "Games" if e.get("X-Rom-Desktop") == "true" else "Shortcuts"})
    for t in items:
        t["id"] = hashlib.sha1(json.dumps([t["name"], t.get("exec"), t.get("action")]).encode()).hexdigest()[:12]
        path = find_icon(t.get("icon"))
        t["icon_url"] = "/icon?name=" + t["icon"] if path else None
    return items

def launch(tile):
    if tile.get("action") == "close":
        subprocess.run(["pkill", "-f", "tvmenu" + "-profile"])
    elif tile.get("exec"):
        subprocess.Popen(tile["exec"], cwd=HOME, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)

class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            html = (HERE / "index.html").read_text().replace("__TOKEN__", TOKEN)
            self.send(200, html.encode(), "text/html; charset=utf-8")
        elif url.path == "/api/tiles":
            self.send(200, json.dumps(tiles()).encode(), "application/json")
        elif url.path == "/icon":
            path = find_icon(parse_qs(url.query).get("name", [""])[0])
            if path:
                self.send(200, Path(path).read_bytes(), mimetypes.guess_type(path)[0] or "image/png")
            else:
                self.send(404, b"", "text/plain")
        else:
            self.send(404, b"", "text/plain")

    def do_POST(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path != "/api/launch" or query.get("token", [""])[0] != TOKEN:
            return self.send(403, b"", "text/plain")
        tile = next((t for t in tiles() if t["id"] == query.get("id", [""])[0]), None)
        if not tile:
            return self.send(404, b"", "text/plain")
        launch(tile)
        self.send(200, b"{}", "application/json")

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
