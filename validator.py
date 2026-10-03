from typing import Any, Dict, List, Optional


REQUIRED_ITEM_FIELDS = ["product_name", "quantity", "unit_price"]


def validate_annotation_schema(annotation: Dict[str, Any]) -> (bool, Optional[str]):
    # Check top-level required fields
    if not isinstance(annotation, dict):
        return False, "annotation_not_object"

    if "bl_number" not in annotation or "bl_date" not in annotation or "supplier_name" not in annotation:
        return False, "missing_top_level_fields"

    items = annotation.get("items")
    if not isinstance(items, list) or len(items) == 0:
        return False, "no_items"

    hard_case = bool(annotation.get("hard_case", False))
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            return False, f"item_{i}_not_object"
        for f in REQUIRED_ITEM_FIELDS:
            if f not in it:
                return False, f"item_{i}_missing_{f}"
        # quantity and unit_price numeric checks
        q = it.get("quantity")
        if q is None:
            if not hard_case:
                return False, f"item_{i}_quantity_null"
        else:
            try:
                float(q)
            except Exception:
                return False, f"item_{i}_quantity_not_numeric"

        up = it.get("unit_price")
        if up is None:
            if not hard_case:
                return False, f"item_{i}_unit_price_null"
        else:
            try:
                float(up)
            except Exception:
                return False, f"item_{i}_unit_price_not_numeric"

    return True, None


def validate_dataset_annotations(annotations: List[Dict[str, Any]]) -> Dict[str, Any]:
    report = {
        "total": len(annotations),
        "valid": 0,
        "invalid": 0,
        "errors": {},
    }

    for ann in annotations:
        ok, reason = validate_annotation_schema(ann)
        if ok:
            report["valid"] += 1
        else:
            report["invalid"] += 1
            key = reason or "unknown"
            report["errors"].setdefault(key, 0)
            report["errors"][key] += 1

    return report
