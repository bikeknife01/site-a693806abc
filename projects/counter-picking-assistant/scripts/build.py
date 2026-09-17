from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SRC = ROOT / "src"
DIST = ROOT / "dist"
DATA = REPO / "projects" / "game-data-encyclopedia" / "public" / "data" / "encyclopedia.json"

if DIST.exists():
    shutil.rmtree(DIST)
shutil.copytree(SRC, DIST)
(DIST / "data").mkdir()
shutil.copy2(DATA, DIST / "data" / "encyclopedia.json")
print(f"built {DIST}")
