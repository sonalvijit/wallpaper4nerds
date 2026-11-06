"""Serve images from the folders configured in the project's .env file.

Run with: python photo_server.py
Then open http://127.0.0.1:8000 in a browser.
"""

from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def read_env(path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE settings without requiring python-dotenv."""
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return values
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip("\"'")
        values[key.strip()] = value
    return values


SETTINGS = read_env(ENV_FILE)
IMAGE_FOLDERS = [item.strip() for item in SETTINGS.get("IMAGE_FOLDERS", "").split(",") if item.strip()]
IMAGE_EXTS = {
    item.strip().lower() if item.strip().startswith(".") else f".{item.strip().lower()}"
    for item in SETTINGS.get("IMAGE_EXTS", ".jpg,.jpeg,.png,.webp,.gif").split(",")
    if item.strip()
}


def configured_roots() -> list[tuple[str, Path]]:
    roots = []
    for folder in IMAGE_FOLDERS:
        candidate = Path(folder)
        if not candidate.is_absolute():
            candidate = BASE_DIR / candidate
        roots.append((folder, candidate.resolve()))
    return roots


ROOTS = configured_roots()


def image_items() -> list[dict[str, str]]:
    items = []
    for label, root in ROOTS:
        if not root.is_dir():
            continue
        for file_path in sorted(root.rglob("*")):
            if not file_path.is_file() or file_path.suffix.lower() not in IMAGE_EXTS:
                continue
            relative = file_path.relative_to(root).as_posix()
            url = "/image/" + quote(label, safe="") + "/" + quote(relative, safe="/")
            items.append({"folder": label, "name": file_path.name, "url": url})
    return items


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Photo library</title><style>
body{font:16px system-ui,sans-serif;margin:0;background:#101218;color:#f1f3f8}header{padding:1rem 2rem;position:sticky;top:0;background:#171a23;display:flex;gap:1rem;align-items:center;flex-wrap:wrap}
h1{font-size:1.25rem;margin:0}input{padding:.65rem;border:1px solid #454b5d;border-radius:.5rem;background:#101218;color:inherit;min-width:15rem}.count{color:#aab1c1}
main{padding:1.25rem}.folder{margin-bottom:2rem}.folder h2{font-size:1.1rem;border-bottom:1px solid #343a49;padding-bottom:.55rem}.folder-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:1rem}.card{background:#1b1f2a;border-radius:.65rem;overflow:hidden}.card img{width:100%;height:180px;object-fit:cover;display:block}.caption{padding:.65rem}.caption strong{display:block;overflow-wrap:anywhere}.caption small{color:#aab1c1}#status{text-align:center;padding:1rem;color:#aab1c1}
</style></head><body><header><h1>Photo library</h1><input id="search" type="search" placeholder="Filter by folder or filename"><span id="count" class="count"></span></header><main id="gallery"></main>
<script>
const gallery=document.querySelector('#gallery'), search=document.querySelector('#search'), count=document.querySelector('#count');
const BATCH_SIZE=36;let photos=[], filtered=[], cursor=0, loading=false;const folderSections=new Map();
function escapeHtml(s){return s.replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]))}
function addBatch(){if(loading)return;loading=true;const batch=filtered.slice(cursor,cursor+BATCH_SIZE);cursor+=batch.length;for(const p of batch){let section=folderSections.get(p.folder);if(!section){section=document.createElement('section');section.className='folder';section.innerHTML=`<h2>${escapeHtml(p.folder)}</h2><div class="folder-grid"></div>`;folderSections.set(p.folder,section);gallery.insertBefore(section,status)}const card=document.createElement('article');card.className='card';card.innerHTML=`<a href="${p.url}" target="_blank" rel="noopener"><img loading="lazy" src="${p.url}" alt="${escapeHtml(p.name)}"></a><div class="caption"><strong>${escapeHtml(p.name)}</strong></div>`;section.querySelector('.folder-grid').appendChild(card)}loading=false;status.textContent=cursor>=filtered.length?(filtered.length?'All photos loaded.':'No photos found.'):'Scroll to load more photos.'}
function reset(){const term=search.value.toLowerCase();filtered=photos.filter(p=>(p.folder+' '+p.name).toLowerCase().includes(term));cursor=0;folderSections.clear();gallery.replaceChildren(status);count.textContent=filtered.length+' photos';addBatch()}
const status=document.createElement('div');status.id='status';status.textContent='Loading photos…';gallery.appendChild(status);
const observer=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting)&&cursor<filtered.length)addBatch()},{rootMargin:'500px'});observer.observe(status);
fetch('/api/images').then(r=>{if(!r.ok)throw new Error('Request failed');return r.json()}).then(data=>{photos=data;reset()}).catch(()=>{status.textContent='Could not load the photo list.'});search.addEventListener('input',reset);
</script></body></html>"""


class PhotoHandler(BaseHTTPRequestHandler):
    server_version = "PhotoServer/1.0"

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/api/images":
            body = json.dumps(image_items()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path.startswith("/image/"):
            self.serve_image(parsed.path)
        else:
            self.send_error(404, "Not found")

    def serve_image(self, request_path: str) -> None:
        parts = request_path[len("/image/"):].split("/", 1)
        if len(parts) != 2:
            self.send_error(404, "Image not found")
            return
        label, relative = unquote(parts[0]), unquote(parts[1])
        root = next((root for name, root in ROOTS if name == label), None)
        if root is None:
            self.send_error(404, "Image not found")
            return
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            self.send_error(404, "Image not found")
            return
        if not candidate.is_file() or candidate.suffix.lower() not in IMAGE_EXTS:
            self.send_error(404, "Image not found")
            return
        try:
            body = candidate.read_bytes()
        except OSError:
            self.send_error(404, "Image not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(os.fspath(candidate))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    host = os.environ.get("PHOTO_SERVER_HOST", DEFAULT_HOST)
    port = int(os.environ.get("PHOTO_SERVER_PORT", str(DEFAULT_PORT)))
    if not ROOTS:
        raise SystemExit(f"No IMAGE_FOLDERS configured in {ENV_FILE}")
    print(f"Serving {len(image_items())} photos at http://{host}:{port}")
    with ThreadingHTTPServer((host, port), PhotoHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
