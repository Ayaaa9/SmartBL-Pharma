import argparse
from collections import defaultdict
from pathlib import Path
from typing import Optional

from config import DatasetConfig, DatasetV2Config, ensure_output_dirs, make_dataset_v2_paths
from data_generator import BLDataGenerator
from renderer import BLRenderer
from previews import generate_previews
from reports import generate_dataset_report
from validator import validate_annotation_schema


def generate_dataset(
    n: int = 1000,
    output_dir: str = "dataset",
    apply_augmentation: bool = True,
) -> None:
    cfg = DatasetConfig()
    cfg.num_documents = n
    cfg.apply_augmentation = apply_augmentation
    cfg.output_dir = Path(output_dir)
    cfg.images_dir = cfg.output_dir / "images"
    cfg.annotations_dir = cfg.output_dir / "annotations"
    cfg.temp_html_dir = cfg.output_dir / "_html"

    ensure_output_dirs(cfg)

    generator = BLDataGenerator(cfg)
    renderer = BLRenderer(cfg)

    seen_signatures = set()
    
    # Calculate split boundaries
    train_count = int(n * cfg.train_ratio)
    val_count = int(n * cfg.val_ratio)
    test_count = n - train_count - val_count
    
    # Track category distribution
    category_stats = defaultdict(lambda: {"total": 0, "train": 0, "val": 0, "test": 0})
    
    def assign_split(idx: int) -> str:
        """Assign document to train/val/test based on index."""
        if idx <= train_count:
            return "train"
        elif idx <= train_count + val_count:
            return "val"
        else:
            return "test"

    def payload_iter():
        for i in range(1, cfg.num_documents + 1):
            if i % 50 == 0:
                print(f"Generation du document {i}/{cfg.num_documents}")
            
            split = assign_split(i)
            
            # Strong uniqueness guard against accidental duplicates.
            while True:
                payload = generator.generate_document(i, split=split)
                signature = (
                    payload["annotation"]["supplier"],
                    payload["annotation"]["bl_number"],
                    tuple(p["raw_text"] for p in payload["annotation"]["products"]),
                )
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    
                    # Track statistics
                    category = payload["annotation"].get("supplier_category", "unknown")
                    category_stats[category]["total"] += 1
                    category_stats[category][split] += 1
                    
                    yield payload
                    break

    renderer.render_many(payload_iter())
    
    # Print statistics
    print(f"\n" + "="*70)
    print(f"✅ Dataset généré avec succès!")
    print(f"="*70)
    print(f"📁 Emplacement: {cfg.output_dir}")
    print(f"📊 Total documents générés: {cfg.num_documents}")
    print(f"\n📂 Structure du dataset:")
    print(f"  ├── images/")
    print(f"  │   ├── train/     ({train_count} documents)")
    print(f"  │   ├── val/       ({val_count} documents)")
    print(f"  │   └── test/      ({test_count} documents)")
    print(f"  └── annotations/")
    print(f"      ├── train/")
    print(f"      ├── val/")
    print(f"      └── test/")
    
    print(f"\n🏢 Distribution par catégorie de fournisseur:")
    for category in sorted(category_stats.keys()):
        stats = category_stats[category]
        pct = stats['total']*100/n
        print(f"  • {category:25s}: {stats['total']:4d} ({pct:5.1f}%)")
        print(f"    ├─ Train: {stats['train']:4d}  │  Val: {stats['val']:4d}  │  Test: {stats['test']:4d}")
    print("="*70)

def generate_dataset_v2(
    n: int = 1000,
    output_dir: str = "dataset_v2",
    apply_augmentation: bool = True,
    hard_case_rate: float = 0.2,
    error_item_rate: float = 0.1,
    ocr_confusion_rate: float = 0.1,
) -> None:
    cfg = DatasetV2Config()
    cfg.num_documents = n
    cfg.apply_augmentation = apply_augmentation
    cfg.output_dir = Path(output_dir)
    cfg.images_dir = cfg.output_dir / "images"
    cfg.annotations_dir = cfg.output_dir / "annotations"
    cfg.html_dir = cfg.output_dir / "_html"
    cfg.reports_dir = cfg.output_dir / "reports"
    cfg.previews_dir = cfg.output_dir / "previews"
    cfg.metadata_dir = cfg.output_dir / "metadata"
    cfg.hard_case_rate = hard_case_rate
    cfg.error_item_rate = error_item_rate
    cfg.ocr_confusion_rate = ocr_confusion_rate
    cfg.validate()

    
    make_dataset_v2_paths(cfg)

    generator = BLDataGenerator(cfg)
    renderer = BLRenderer(cfg)

    split_counts = {
        "train": int(n * cfg.train_ratio),
        "val": int(n * cfg.val_ratio),
        "test": n - int(n * cfg.train_ratio) - int(n * cfg.val_ratio),
    }

    def assign_split(idx: int) -> str:
        if idx <= split_counts["train"]:
            return "train"
        if idx <= split_counts["train"] + split_counts["val"]:
            return "val"
        return "test"

    invalid = 0

    def payload_iter():
        nonlocal invalid
        generated = 0
        idx = 0
        while generated < cfg.num_documents:
            idx += 1
            split = assign_split(idx)
            if idx % 50 == 0:
                print(f"Generation v2 du document {generated + 1}/{cfg.num_documents}")
            payload = generator.generate_document(idx, split=split)
            ok, reason = validate_annotation_schema(payload["annotation"])
            if not ok:
                invalid += 1
                print(f"  ⚠️  Annotation invalide pour {payload['doc_id']}: {reason}")
                continue
            generated += 1
            yield payload

    renderer.render_many(payload_iter())
    report = generate_dataset_report(cfg.output_dir)
    generate_previews(cfg.output_dir, count=20)

    print(f"\n{'='*70}")
    print(f"✅ Dataset v2 généré avec succès!")
    print(f"📁 Emplacement: {cfg.output_dir}")
    print(f"📊 Documents demandés: {cfg.num_documents}")
    print(f"📉 Invalides rejetés: {invalid}")
    print(f"📈 Rapport: {cfg.reports_dir / 'dataset_v2_report.json'}")
    print(f"🖼️  Previews: {cfg.previews_dir}")
    print(f"📂 Structure: images/train|val|test + annotations/train|val|test")
    print(f"{'='*70}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic Moroccan BL dataset")
    parser.add_argument("-n", "--num-docs", type=int, default=1000)
    parser.add_argument("--output-dir", type=str, default="dataset_v2")
    parser.add_argument("--dataset-version", type=str, choices=["v1", "v2"], default="v2")
    parser.add_argument(
        "--no-augmentation",
        action="store_true",
        help="Disable image realism augmentation stage",
    )
    parser.add_argument(
        "--hard-case-rate",
        type=float,
        default=0.2,
        help="Rate of hard cases to be included in the dataset",
    )
    parser.add_argument(
        "--error-item-rate",
        type=float,
        default=0.1,
        help="Rate of items with errors to be included in the dataset",
    )
    parser.add_argument(
        "--ocr-confusion-rate",
        type=float,
        default=0.1,
        help="Rate of OCR confusion errors to be introduced into the dataset",
    )
    parser.add_argument(
        "--apply-augmentation",
        action="store_true",
        help="Apply augmentations to the images (rotation, blur, etc.)",
    )
    
    args = parser.parse_args()

    # Run the dataset generation for version v2
    if generate_dataset_v2(
        n=args.num_docs,
        output_dir=args.output_dir,
        apply_augmentation=not args.no_augmentation,
        hard_case_rate=args.hard_case_rate,
        error_item_rate=args.error_item_rate,
        ocr_confusion_rate=args.ocr_confusion_rate,
    ) is not None:
        print("Dataset v2 generation completed with issues. Check logs for details.")
    else:
        generate_dataset(
            n=args.num_docs,
            output_dir=args.output_dir,
            apply_augmentation=not args.no_augmentation,
        )
