# server/client/__init__.py
import os
from pathlib import Path
from flask import Blueprint, send_from_directory

HERE = Path(__file__).resolve().parent
CLIENT_DIST = HERE / "static"          # path to server/client/static
ASSETS_DIR = CLIENT_DIST / "assets"

ilm_bp = Blueprint(
    "ilm",
    __name__,
    static_folder=str(ASSETS_DIR),     # hashed assets
    static_url_path="/ilm/assets",     # they’ll be at /ilm/assets/...
)

# Serve index.html for /ilm
@ilm_bp.route("/")
def ilm_index():
    return send_from_directory(str(CLIENT_DIST), "index.html")

# Serve assets explicitly (optional, static above already handles /ilm/assets/*)
@ilm_bp.route("/assets/<path:filename>")
def ilm_assets(filename):
    return send_from_directory(str(ASSETS_DIR), filename)

# History fallback for Vue Router: any non-asset path under /ilm returns index.html
@ilm_bp.route("/<path:path>")
def ilm_spa(path: str):
    # Let /ilm/assets/* be handled by static; everything else => index.html
    if path.startswith("assets/"):
        # This path is normally served by the blueprint's static; keep for safety.
        return send_from_directory(str(ASSETS_DIR), path[len("assets/"):])
    return send_from_directory(str(CLIENT_DIST), "index.html")
