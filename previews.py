from __future__ import annotations

import json
import random
import shutil
from pathlib import Path
from typing import Dict, List


def _copy_pair(image_src: Path, annotation_src: Path, preview_dir: Path) -> None:
    preview_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image_src, preview_dir / image_src.name)
    shutil.copy2(annotation_src, preview_dir / annotation_src.name)


def generate_previews(dataset_root: Path, count: int = 20) -> List[Path]:
    images_root = dataset_root / "images"
    annotations_root = dataset_root / "annotations"
    previews_root = dataset_root / "previews"
    previews_root.mkdir(parents=True, exist_ok=True)

    candidates: List[Dict[str, Path]] = []
    for split in ["train", "val", "test"]:
        for ann_path in sorted((annotations_root / split).glob("*.json")):
            img_path = images_root / split / f"{ann_path.stem}.png"
            if img_path.exists():
                candidates.append({"split": split, "annotation": ann_path, "image": img_path})

    if not candidates:
        return []

    rng = random.Random(42)
    selected: List[Dict[str, Path]] = []
    seen = set()

    # stratify: easy/medium/hard and missing lot/expiry if available
    def pick(predicate, wanted: int) -> None:
        pool = [c for c in candidates if c["annotation"].stem not in seen and predicate(c)]
        rng.shuffle(pool)
        for item in pool[:wanted]:
            seen.add(item["annotation"].stem)
            selected.append(item)

    def load_ann(c):
        with c["annotation"].open("r", encoding="utf-8") as f:
            return json.load(f)

    pick(lambda c: load_ann(c).get("difficulty") == "easy", 5)
    pick(lambda c: load_ann(c).get("difficulty") == "medium", 5)
    pick(lambda c: load_ann(c).get("difficulty") == "hard", 5)
    pick(lambda c: any(item.get("lot_number") is None or item.get("expiry_date") is None for item in load_ann(c).get("items", [])), 5)

    if len(selected) < count:
        remaining = [c for c in candidates if c["annotation"].stem not in seen]
        rng.shuffle(remaining)
        selected.extend(remaining[: count - len(selected)])

    copied: List[Path] = []
    for idx, item in enumerate(selected[:count], start=1):
        preview_dir = previews_root / f"sample_{idx:02d}"
        _copy_pair(item["image"], item["annotation"], preview_dir)
        copied.append(preview_dir)

    return copied
