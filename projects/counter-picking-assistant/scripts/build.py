from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"
DATA = REPO / "projects" / "game-data-encyclopedia" / "public" / "data" / "encyclopedia.json"
PROFILE_MODULE = REPO / "projects" / "shared-data-foundation" / "src" / "profile" / "player-profile.mjs"
PROFILE_STYLES = REPO / "projects" / "shared-data-foundation" / "src" / "profile" / "player-profile.css"

if DIST.exists():
    shutil.rmtree(DIST)
shutil.copytree(SRC, DIST)
shutil.copy2(PROFILE_MODULE, DIST / "player-profile.mjs")
shutil.copy2(PROFILE_STYLES, DIST / "player-profile.css")
(DIST / "data").mkdir()
shutil.copy2(DATA, DIST / "data" / "encyclopedia.json")
print(f"built {DIST}")
