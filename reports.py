from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


def _safe_load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def generate_dataset_report(dataset_root: Path) -> Dict[str, Any]:
    annotations_root = dataset_root / "annotations"
    report_dir = dataset_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    split_files = {
        split: sorted((annotations_root / split).glob("*.json"))
        for split in ["train", "val", "test"]
    }

    docs: List[Dict[str, Any]] = []
    for split, files in split_files.items():
        for file_path in files:
            annotation = _safe_load_json(file_path)
            annotation["_split"] = split
            docs.append(annotation)

    difficulty_counter = Counter()
    supplier_counter = Counter()
    template_counter = Counter()
    item_counts: List[int] = []
    lot_present = 0
    expiry_present = 0
    quantity_integer = 0
    quantity_decimal = 0
    prices: List[float] = []
    invalid_labels = 0
    rejected_docs = 0
    review_flags = Counter()

    for ann in docs:
        items = ann.get("items", [])
        item_counts.append(len(items))
        difficulty_counter[str(ann.get("difficulty", "unknown"))] += 1
        supplier_counter[str(ann.get("supplier_name", "unknown"))] += 1
        template_counter[str(ann.get("template_family", ann.get("template", "unknown")))] += 1
        review_flags.update(ann.get("review_flags", []))
        if ann.get("render_error"):
            rejected_docs += 1

        for item in items:
            lot = item.get("lot_number")
            expiry = item.get("expiry_date")
            if lot not in (None, ""):
                lot_present += 1
            if expiry not in (None, ""):
                expiry_present += 1

            quantity = item.get("quantity")
            if quantity is not None:
                try:
                    q = float(quantity)
                    if q.is_integer():
                        quantity_integer += 1
                    else:
                        quantity_decimal += 1
                except Exception:
                    invalid_labels += 1

            unit_price = item.get("unit_price")
            if unit_price is not None:
                try:
                    prices.append(float(unit_price))
                except Exception:
                    invalid_labels += 1
            else:
                invalid_labels += 1

    total_items = sum(item_counts) or 1
    report = {
        "dataset_root": str(dataset_root),
        "documents_total": len(docs),
        "split_counts": {split: len(files) for split, files in split_files.items()},
        "difficulty_distribution": dict(difficulty_counter),
        "supplier_distribution": dict(supplier_counter),
        "template_distribution": dict(template_counter),
        "items": {
            "mean": round(sum(item_counts) / len(item_counts), 2) if item_counts else 0.0,
            "min": min(item_counts) if item_counts else 0,
            "max": max(item_counts) if item_counts else 0,
        },
        "rates": {
            "lot_present": round(lot_present / total_items, 4),
            "lot_null": round(1.0 - (lot_present / total_items), 4),
            "expiry_present": round(expiry_present / total_items, 4),
            "expiry_null": round(1.0 - (expiry_present / total_items), 4),
            "quantity_integer": round(quantity_integer / max(1, (quantity_integer + quantity_decimal)), 4),
            "quantity_decimal": round(quantity_decimal / max(1, (quantity_integer + quantity_decimal)), 4),
        },
        "prices": {
            "min": round(min(prices), 2) if prices else 0.0,
            "max": round(max(prices), 2) if prices else 0.0,
            "avg": round(sum(prices) / len(prices), 2) if prices else 0.0,
        },
        "invalid_labels": invalid_labels,
        "rejected_docs": rejected_docs,
        "review_flags": dict(review_flags),
    }

    json_path = report_dir / "dataset_v2_report.json"
    csv_path = report_dir / "dataset_v2_summary.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["documents_total", report["documents_total"]])
        for split, count in report["split_counts"].items():
            writer.writerow([f"split_{split}", count])
        writer.writerow(["items_mean", report["items"]["mean"]])
        writer.writerow(["items_min", report["items"]["min"]])
        writer.writerow(["items_max", report["items"]["max"]])
        writer.writerow(["lot_present_rate", report["rates"]["lot_present"]])
        writer.writerow(["expiry_present_rate", report["rates"]["expiry_present"]])
        writer.writerow(["quantity_integer_rate", report["rates"]["quantity_integer"]])
        writer.writerow(["quantity_decimal_rate", report["rates"]["quantity_decimal"]])
        writer.writerow(["price_avg", report["prices"]["avg"]])
        writer.writerow(["price_min", report["prices"]["min"]])
        writer.writerow(["price_max", report["prices"]["max"]])
        writer.writerow(["invalid_labels", report["invalid_labels"]])
        writer.writerow(["rejected_docs", report["rejected_docs"]])

    return report
