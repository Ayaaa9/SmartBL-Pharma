from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any, Dict, List

# ============================================================================
# SUPPLIER CATEGORIZATION SYSTEM
# ============================================================================
# Maps supplier names to their category (pharma_distrib, facture_premium, ticket_compact, dossier_administratif)

SUPPLIER_CATEGORIES: Dict[str, str] = {
    # Distributeurs pharma standard
    "PHARMANORD": "pharma_distrib",
    "KENIPHARMA": "pharma_distrib",
    "REPHAL": "pharma_distrib",
    "COOPER PHARMA REPARTITION": "pharma_distrib",
    "COOPER CHAOUIA": "pharma_distrib",
    "COOPER TENSIFT": "pharma_distrib",
    "COOPER BENISNASSEN": "pharma_distrib",
    "PHARMACOOP": "pharma_distrib",
    "PHARMAEST": "pharma_distrib",
    "ORIENTAL MEDICA": "pharma_distrib",
    "MEDIREP": "pharma_distrib",
    "DISTRIPHAK": "pharma_distrib",
    "DISTRIPHAK 2ème dépôt": "pharma_distrib",
    "DISMEDIC": "pharma_distrib",
    "DISPHAT": "pharma_distrib",
    "DIPHARM": "pharma_distrib",
    "DISPHANAD": "pharma_distrib",
    "REPHAK": "pharma_distrib",
    "REPHAR": "pharma_distrib",
    
    # Factures premium et haut de gamme
    "SARP": "facture_premium",
    "BUMAGECO": "facture_premium",
    "GIPHAR": "facture_premium",
    "GPM": "facture_premium",
    "MAREPHA": "facture_premium",
    "RECAMED": "facture_premium",
    "CPM": "facture_premium",
    "CPRE": "facture_premium",
    
    # Tickets compacts
    "GLOBALDIS": "ticket_compact",
    "MEDEXPERT": "ticket_compact",
    "ORP": "ticket_compact",
    "MD5": "ticket_compact",
    "MEDICOL": "ticket_compact",
    "GDIS": "ticket_compact",
    "COPHAG": "ticket_compact",
    "COPHADIS": "ticket_compact",
    
    # Dossiers administratifs
    "AFRIC MED DISTRIBUTION": "dossier_administratif",
    "LODIMED": "dossier_administratif",
    "SOPHATLANTIC": "dossier_administratif",
    "SOPHAFAS": "dossier_administratif",
    "SOFASAIS": "dossier_administratif",
    "SOPHAGHARB": "dossier_administratif",
    "SOPHASALE": "dossier_administratif",
    "SOPHANORD": "dossier_administratif",
    "SERP": "dossier_administratif",
    "PHARMAMEC": "dossier_administratif",
    "GPF": "dossier_administratif",
    "PHARMASMIR": "dossier_administratif",
}

# ============================================================================
# LAYOUT VARIANTS WITH CATEGORY-SPECIFIC STYLING
# ============================================================================

LAYOUT_VARIANTS: List[Dict[str, Any]] = [
    {
        "key": "ledger",
        "label": "Ledger",
        "title": "BON DE LIVRAISON",
        "header_color": "#2d4a7c",
        "accent_color": "#6f8fb9",
        "page_bg": "#eef2f7",
        "border_color": "#8392a8",
        "table_bg": "#ffffff",
        "table_head_bg": "#dce5f4",
        "table_alt_bg": "#f7faff",
        "footer_bg": "#f0f5fb",
        "column_order": ["code", "designation", "qty", "pph", "unit_price", "line_total"],
        "totals_labels": ["TOTAL HT", "TVA", "NET A PAYER"],
        "footer": "Les produits sont controles avant expedition et doivent etre verifies a reception.",
        "show_lot": False,
        "show_peremption": False,
        "show_remise": False,
        "show_pph": True,
        "show_tva": False,
        "show_code": True,
        "medicine_band": "balanced",
        "body_kind": "ledger",
    },
    {
        "key": "clinical",
        "label": "Clinical",
        "title": "BON DE LIVRAISON MEDICAL",
        "header_color": "#196b7d",
        "accent_color": "#4ea9ba",
        "page_bg": "#edf7f9",
        "border_color": "#7d9da4",
        "table_bg": "#ffffff",
        "table_head_bg": "#d8f0f5",
        "table_alt_bg": "#f4fbfd",
        "footer_bg": "#eef8fb",
        "column_order": ["designation", "lot", "qty", "unit_price", "peremption", "line_total"],
        "totals_labels": ["MONTANT HT", "MONTANT TVA", "TOTAL TTC"],
        "footer": "Suivi lot et peremption privilegie pour les flux sensibles.",
        "show_lot": True,
        "show_peremption": True,
        "show_remise": False,
        "show_pph": False,
        "show_tva": False,
        "show_code": False,
        "medicine_band": "low",
        "body_kind": "clinical",
    },
    {
        "key": "receipt",
        "label": "Receipt",
        "title": "BON DE LIVRAISON",
        "header_color": "#6d4a2b",
        "accent_color": "#c49b5c",
        "page_bg": "#f6f0e7",
        "border_color": "#9b866f",
        "table_bg": "#fffdf9",
        "table_head_bg": "#f1e3cd",
        "table_alt_bg": "#fdf8f0",
        "footer_bg": "#faf3e8",
        "column_order": ["designation", "qty", "unit_price", "tva", "line_total"],
        "totals_labels": ["TOTAL H.T", "TVA", "TOTAL GENERAL"],
        "footer": "Format compact type ticket pour lectures rapides et scans mobiles.",
        "show_lot": False,
        "show_peremption": False,
        "show_remise": False,
        "show_pph": False,
        "show_tva": True,
        "show_code": False,
        "medicine_band": "mixed",
        "body_kind": "receipt",
    },
    {
        "key": "invoice",
        "label": "Invoice",
        "title": "BON DE LIVRAISON / FACTURE",
        "header_color": "#5f3f88",
        "accent_color": "#9b79cc",
        "page_bg": "#f4effa",
        "border_color": "#9e8db7",
        "table_bg": "#ffffff",
        "table_head_bg": "#e2d9f3",
        "table_alt_bg": "#faf7ff",
        "footer_bg": "#f2ebfb",
        "column_order": ["code", "designation", "qty", "unit_price", "remise", "line_total"],
        "totals_labels": ["MONTANT HT", "TVA FACTUREE", "TOTAL TTC"],
        "footer": "Facturation detaillee avec remise et synthese des montants.",
        "show_lot": False,
        "show_peremption": False,
        "show_remise": True,
        "show_pph": False,
        "show_tva": False,
        "show_code": True,
        "medicine_band": "premium",
        "body_kind": "invoice",
    },
    {
        "key": "dossier",
        "label": "Dossier",
        "title": "DOSSIER DE LIVRAISON",
        "header_color": "#214d42",
        "accent_color": "#62a38f",
        "page_bg": "#eef5f1",
        "border_color": "#88a79f",
        "table_bg": "#ffffff",
        "table_head_bg": "#d9ebe2",
        "table_alt_bg": "#f7fbf9",
        "footer_bg": "#edf7f2",
        "column_order": ["designation", "code", "qty", "pph", "tva", "peremption", "line_total"],
        "totals_labels": ["SOUS TOTAL", "TVA", "TOTAL TTC"],
        "footer": "Dossier administratif avec repere code produit et peremption.",
        "show_lot": False,
        "show_peremption": True,
        "show_remise": False,
        "show_pph": True,
        "show_tva": True,
        "show_code": True,
        "medicine_band": "mid",
        "body_kind": "dossier",
    },
    {
        "key": "executive",
        "label": "Executive",
        "title": "BON DE LIVRAISON EXECUTIF",
        "header_color": "#28303f",
        "accent_color": "#7d8699",
        "page_bg": "#eceff4",
        "border_color": "#8f97a4",
        "table_bg": "#ffffff",
        "table_head_bg": "#dde3ec",
        "table_alt_bg": "#f7f9fc",
        "footer_bg": "#eef2f8",
        "column_order": ["code", "designation", "qty", "unit_price", "pph", "line_total"],
        "totals_labels": ["TOTAL NET", "TVA", "TOTAL A PAYER"],
        "footer": "Version executee avec bloc total, cachet et synthese en colonne.",
        "show_lot": False,
        "show_peremption": False,
        "show_remise": False,
        "show_pph": True,
        "show_tva": False,
        "show_code": True,
        "medicine_band": "premium",
        "body_kind": "executive",
    },
    {
        "key": "compact",
        "label": "Compact",
        "title": "BON DE LIVRAISON",
        "header_color": "#7a3d3d",
        "accent_color": "#c46f6f",
        "page_bg": "#f9f0f0",
        "border_color": "#ab8d8d",
        "table_bg": "#fffdfd",
        "table_head_bg": "#f5dddd",
        "table_alt_bg": "#fff7f7",
        "footer_bg": "#fbefef",
        "column_order": ["designation", "qty", "unit_price", "line_total"],
        "totals_labels": ["TOTAL H.T", "TVA", "TOTAL TTC"],
        "footer": "Format minimal dense pour des BL rapides et peu chargés.",
        "show_lot": False,
        "show_peremption": False,
        "show_remise": False,
        "show_pph": False,
        "show_tva": False,
        "show_code": False,
        "medicine_band": "low",
        "body_kind": "compact",
    },
    {
        "key": "technical",
        "label": "Technical",
        "title": "BON TECHNIQUE DE LIVRAISON",
        "header_color": "#39515e",
        "accent_color": "#7aa4b4",
        "page_bg": "#edf2f4",
        "border_color": "#8aa0ab",
        "table_bg": "#ffffff",
        "table_head_bg": "#dce8ef",
        "table_alt_bg": "#f6fafc",
        "footer_bg": "#eef5f8",
        "column_order": ["designation", "code", "lot", "qty", "unit_price", "tva", "line_total"],
        "totals_labels": ["SOUS TOTAL", "TVA", "TOTAL GENERAL"],
        "footer": "Bloc technique avec suivi lot et TVA detaillee.",
        "show_lot": True,
        "show_peremption": False,
        "show_remise": False,
        "show_pph": False,
        "show_tva": True,
        "show_code": True,
        "medicine_band": "mixed",
        "body_kind": "technical",
    },
    {
        "key": "premium",
        "label": "Premium",
        "title": "FACTURE LIVRAISON PREMIUM",
        "header_color": "#8a5a14",
        "accent_color": "#d3a24a",
        "page_bg": "#f9f4ea",
        "border_color": "#b39b73",
        "table_bg": "#fffdf8",
        "table_head_bg": "#f0dfba",
        "table_alt_bg": "#fcf7ec",
        "footer_bg": "#fbf1dd",
        "column_order": ["code", "designation", "lot", "qty", "unit_price", "remise", "line_total"],
        "totals_labels": ["TOTAL HT", "TVA", "TOTAL TTC"],
        "footer": "Presentation premium avec remise et references de lot.",
        "show_lot": True,
        "show_peremption": False,
        "show_remise": True,
        "show_pph": False,
        "show_tva": False,
        "show_code": True,
        "medicine_band": "premium",
        "body_kind": "premium",
    },
]


TEMPLATE_FAMILIES: Dict[str, Dict[str, Any]] = {
    "cooper": {"layout": "ledger", "weight": 0.18},
    "dipharm": {"layout": "clinical", "weight": 0.14},
    "rephal": {"layout": "receipt", "weight": 0.14},
    "sarp": {"layout": "invoice", "weight": 0.14},
    "kenipharma": {"layout": "compact", "weight": 0.10},
    "pharmanord": {"layout": "technical", "weight": 0.10},
    "bumageco": {"layout": "executive", "weight": 0.10},
    "default": {"layout": "ledger", "weight": 0.10},
}


def supplier_slug(txt: str) -> str:
    normalized = unicodedata.normalize("NFKD", txt)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower().strip()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text)
    ascii_text = re.sub(r"-{2,}", "-", ascii_text).strip("-")
    return ascii_text or "supplier"


def supplier_category(supplier_name: str) -> str:
    """
    Get the category (pharma_distrib, facture_premium, ticket_compact, dossier_administratif)
    for a supplier, using stored mappings or hash-based fallback.
    """
    # Try exact match first
    for key in SUPPLIER_CATEGORIES:
        if supplier_name.upper() == key.upper():
            return SUPPLIER_CATEGORIES[key]
    
    # Fallback: use hash-based distribution
    slug = supplier_slug(supplier_name)
    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()
    categories = ["pharma_distrib", "facture_premium", "ticket_compact", "dossier_administratif"]
    index = int(digest[:8], 16) % len(categories)
    return categories[index]


def supplier_template_path(supplier_name: str) -> str:
    return f"suppliers/{supplier_slug(supplier_name)}.html"


def layout_variant_for_supplier(supplier_name: str) -> Dict[str, Any]:
    slug = supplier_slug(supplier_name)
    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()
    index = int(digest[:8], 16) % len(LAYOUT_VARIANTS)
    variant = dict(LAYOUT_VARIANTS[index])
    variant["slug"] = slug
    variant["supplier_name"] = supplier_name
    variant["theme_seed"] = int(digest[8:16], 16)
    variant["accent_2"] = f"#{digest[16:22]}"
    variant["accent_3"] = f"#{digest[22:28]}"
    return variant


def template_family_for_supplier(supplier_name: str) -> str:
    name = supplier_name.upper()
    if "COOPER" in name:
        return "cooper"
    if "DIPHARM" in name:
        return "dipharm"
    if "REPHAL" in name:
        return "rephal"
    if "SARP" in name or "S.A.R.P" in name:
        return "sarp"
    if "KENIPHARMA" in name:
        return "kenipharma"
    if "PHARMANORD" in name:
        return "pharmanord"
    if "BUMAGECO" in name:
        return "bumageco"
    return "default"


def template_layout_for_supplier(supplier_name: str) -> str:
    family = template_family_for_supplier(supplier_name)
    return TEMPLATE_FAMILIES.get(family, TEMPLATE_FAMILIES["default"])["layout"]


def supplier_profile_for_supplier(supplier_name: str) -> Dict[str, Any]:
    variant = layout_variant_for_supplier(supplier_name)
    digest = hashlib.sha1(variant["slug"].encode("utf-8")).hexdigest()
    palette = [
        variant["header_color"],
        variant["accent_color"],
        variant["accent_2"],
        variant["accent_3"],
        "#2f4f4f",
        "#5b6770",
        "#7c4d3e",
        "#3e6b5e",
    ]

    category = supplier_category(supplier_name)

    return {
        "layout_variant": variant["key"],
        "layout_label": variant["label"],
        "body_kind": variant["body_kind"],
        "title": variant["title"],
        "header_color": variant["header_color"],
        "accent_color": variant["accent_color"],
        "accent_2": variant["accent_2"],
        "accent_3": variant["accent_3"],
        "page_bg": variant["page_bg"],
        "border_color": variant["border_color"],
        "table_bg": variant["table_bg"],
        "table_head_bg": variant["table_head_bg"],
        "table_alt_bg": variant["table_alt_bg"],
        "footer_bg": variant["footer_bg"],
        "column_order": variant["column_order"],
        "totals_labels": variant["totals_labels"],
        "footer": variant["footer"],
        "show_lot": variant["show_lot"],
        "show_peremption": variant["show_peremption"],
        "show_remise": variant["show_remise"],
        "show_pph": variant["show_pph"],
        "show_tva": variant["show_tva"],
        "show_code": variant["show_code"],
        "medicine_band": variant["medicine_band"],
        "palette": palette,
        "palette_seed": int(digest[:8], 16),
        "supplier_category": category,
        "category_label": {
            "pharma_distrib": "Distributeur Pharma",
            "facture_premium": "Facture Premium",
            "ticket_compact": "Ticket Compact",
            "dossier_administratif": "Dossier Administratif",
        }.get(category, "Standard"),
    }
