from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
if DIST.exists():
    shutil.rmtree(DIST)
shutil.copytree(ROOT / "src", DIST)
(DIST / ".nojekyll").touch()
print(f"built {DIST}")
