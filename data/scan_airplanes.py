#!/usr/bin/env python3
"""
Scan static/assets/3d/airplanes/ → generate models.json

Run with:

$ python -m scripts.scan_airplanes
"""

import json, hashlib
from pathlib import Path
import trimesh

# Paths
DEST     = Path("static/assets/3d/airplanes")
MANIFEST = Path("static/assets/3d/models.json")

# SHA256 hash
def sha256(p: Path) -> str:
    return hashlib.file_digest(open(p, "rb"), "sha256").hexdigest()

# Count triangles
def triangle_count(glb: Path) -> int:
    try:
        m = trimesh.load(glb)

        if isinstance(m, trimesh.Trimesh):
            return int(m.faces.shape[0])

        elif isinstance(m, trimesh.Scene):
            return sum(len(g.faces) for g in m.geometry.values())

        else:
            print(f"⚠️ Unknown mesh type for {glb.name} → skipping")
            return 0

    except Exception as e:
        print(f"⚠️ Error loading {glb.name}: {e}")
        return 0

# Main
def main():
    records = []

    glb_files = sorted(DEST.glob("*.glb"))

    if not glb_files:
        print("⚠️ No .glb models found in static/assets/3d/airplanes/")
        return

    for glb in glb_files:
        print(f"🔍 Processing {glb.name}")

        tris = triangle_count(glb)
        sha  = sha256(glb)

        # Optional credits (.txt sidecar file)
        txt_path = glb.with_suffix(".txt")
        credit = txt_path.read_text().strip() if txt_path.exists() else "Unknown Author"

        records.append({
            "id":         glb.stem,
            "name":       glb.stem.replace("-", " ").replace("_", " ").title(),
            "author":     credit,
            "author_url": "",  # Optional — you can edit later
            "license":    "CC Attribution",  # Assumed if you downloaded manually
            "path": f"static/assets/3d/airplanes/{glb.name}",
            "tris":       tris,
            "sha256":     sha
        })

    # Save manifest
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(records, indent=2))
    print(f"\n✅ Wrote {len(records)} models to {MANIFEST}")

# Entry
if __name__ == "__main__":
    main()
