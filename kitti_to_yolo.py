from pathlib import Path
from collections import Counter

# ========= KONFIG =========
ROOT = Path("/mnt/c/datasets/gta")   # Windows nativ: Path(r"C:\datasets\gta")
IMG_DIR      = ROOT / "extracted_images" / "image_2"
KITTI_DIR    = ROOT / "label_2"
YOLO_OUT_DIR = ROOT / "labels_yolo" / "image_2"

IMG_W, IMG_H = 1920, 1080            # PreSIL-Auflösung

# 5 Klassen mit fester Reihenfolge
CLASSES = ["car", "truck", "bus", "person", "trailer"]

# Mapping: welche Raw-Typen auf welche Klasse gehen
MAP_CAR     = {"car"}
MAP_TRUCK   = {"truck"}
MAP_BUS     = {"bus"}
MAP_PERSON  = {"pedestrian", "person", "person_sitting"}
MAP_TRAILER = {"trailer"}

CLASS_TO_ID = {
    **{k: 0 for k in MAP_CAR},
    **{k: 1 for k in MAP_TRUCK},
    **{k: 2 for k in MAP_BUS},
    **{k: 3 for k in MAP_PERSON},
    **{k: 4 for k in MAP_TRAILER},
}
WRITE_EMPTY_FILES = True  # leere .txt pro Bild, falls keine gültigen Boxen
# =========================

def kitti_line_to_yolo(parts):
    """KITTI: class trunc occl alpha x1 y1 x2 y2 ...  -> 'cid xc yc w h' (YOLO)"""
    if len(parts) < 8:
        return None
    key = parts[0].lower()
    cid = CLASS_TO_ID.get(key)
    if cid is None:
        return None
    try:
        x1, y1, x2, y2 = map(float, parts[4:8])
    except Exception:
        return None
    # clamp + checks
    x1 = max(0.0, min(x1, IMG_W)); x2 = max(0.0, min(x2, IMG_W))
    y1 = max(0.0, min(y1, IMG_H)); y2 = max(0.0, min(y2, IMG_H))
    if not (x2 > x1 and y2 > y1):
        return None
    xc = ((x1 + x2) / 2.0) / IMG_W
    yc = ((y1 + y2) / 2.0) / IMG_H
    w  = (x2 - x1) / IMG_W
    h  = (y2 - y1) / IMG_H
    if not (0 <= xc <= 1 and 0 <= yc <= 1 and 0 < w <= 1 and 0 < h <= 1):
        return None
    return f"{cid} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}"

def main():
    YOLO_OUT_DIR.mkdir(parents=True, exist_ok=True)

    img_stems   = {p.stem for p in IMG_DIR.glob("*.png")}
    kitti_files = list(KITTI_DIR.glob("*.txt"))

    made = empty = skipped = 0
    seen, kept, dropped = Counter(), Counter(), Counter()

    for lab in kitti_files:
        stem = lab.stem
        if stem not in img_stems:
            skipped += 1
            continue

        out_lines = []
        with open(lab, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                parts = line.split()
                raw = parts[0].lower()
                seen[raw] += 1
                y = kitti_line_to_yolo(parts)
                if y:
                    cls_id = int(y.split()[0])
                    kept[CLASSES[cls_id]] += 1
                    out_lines.append(y)
                else:
                    dropped[raw] += 1

        out = YOLO_OUT_DIR / f"{stem}.txt"
        if out_lines:
            out.write_text("\n".join(out_lines) + "\n")
            made += 1
        else:
            if WRITE_EMPTY_FILES:
                out.write_text("")
                empty += 1
            else:
                skipped += 1

    print("Konvertierung abgeschlossen.")
    print(f"  YOLO-Dateien geschrieben: {made}")
    print(f"  Leere Dateien:            {empty}")
    print(f"  Übersprungen (kein Bild): {skipped}")
    print(f"Output: {YOLO_OUT_DIR}")
    print("YOLO-Klassen:", CLASSES)

    print("\nTop gesehene Typen (raw):")
    for k,v in seen.most_common(10): print(f"{v:7d}  {k}")
    print("\nBehalten (nach Mapping):")
    for k,v in kept.most_common(): print(f"{v:7d}  {k}")
    print("\nGedroppt (Top 10):")
    for k,v in dropped.most_common(10): print(f"{v:7d}  {k}")

if __name__ == "__main__":
    main()
