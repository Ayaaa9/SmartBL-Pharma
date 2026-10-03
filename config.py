from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class DatasetConfig:
    project_root: Path = Path(__file__).resolve().parent
    user_home: Path = Path.home()
    data_dir: Path = project_root / "data"
    output_dir: Path = project_root / "dataset"
    images_dir: Path = output_dir / "images"
    annotations_dir: Path = output_dir / "annotations"
    templates_dir: Path = project_root / "templates"
    temp_html_dir: Path = output_dir / "_html"

    suppliers_csv_path: Path = data_dir / "suppliers.csv"
    suppliers_csv_fallbacks: List[Path] = field(
        default_factory=lambda: [
            Path.home() / "Desktop" / "suppliers_202604231724.csv",
            Path.home() / "suppliers_202604231722.csv",
            Path.home() / "Desktop" / "suppliers.csv",
        ]
    )
    medicines_file_candidates: List[Path] = field(
        default_factory=lambda: [
            Path(__file__).resolve().parent / "data" / "wellys_db.xlsx",
            Path.home() / "Downloads" / "wellys_db.xlsx",
            Path(__file__).resolve().parent / "data" / "medicines.csv",
            Path(__file__).resolve().parent / "data" / "medicaments.csv",
        ]
    )

    num_documents: int = 1000
    random_seed: int = 42
    apply_augmentation: bool = True

    image_format: str = "png"
    image_quality: int = 95

    min_products_per_doc: int = 1
    max_products_per_doc: int = 15

    template_files: List[str] = field(
        default_factory=lambda: [
            "pharmanord.html",
            "bumageco.html",
            "kenipharma.html",
            "rephal.html",
            "sarp.html",
        ]
    )

    style_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "clean": 0.35,
            "dense": 0.30,
            "receipt": 0.20,
            "colored": 0.15,
        }
    )

    # Dataset splits configuration
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15

    # Supplier categories with distinctive styles
    supplier_categories: Dict[str, Dict[str, any]] = field(
        default_factory=lambda: {
            "pharma_distrib": {
                "label": "Distributeur Pharma",
                "description": "Distribution pharmaceutique standard",
                "header_color": "#2d5a3d",
                "accent_color": "#4a9b6f",
                "page_bg": "#f0f5f2",
                "table_head_bg": "#d1e8d8",
                "border_style": "solid",
                "logo_type": "text_badge",
                "min_products": 8,
                "max_products": 20,
                "show_lot": True,
                "show_peremption": True,
            },
            "facture_premium": {
                "label": "Facture Premium",
                "description": "Facture haut de gamme et détaillée",
                "header_color": "#8a5a14",
                "accent_color": "#d3a24a",
                "page_bg": "#f9f4ea",
                "table_head_bg": "#f0dfba",
                "border_style": "double",
                "logo_type": "premium_seal",
                "min_products": 5,
                "max_products": 15,
                "show_lot": True,
                "show_peremption": False,
            },
            "ticket_compact": {
                "label": "Ticket Compact",
                "description": "Format compact et minimaliste",
                "header_color": "#6d4a2b",
                "accent_color": "#c49b5c",
                "page_bg": "#f6f0e7",
                "table_head_bg": "#f1e3cd",
                "border_style": "dotted",
                "logo_type": "minimal_stamp",
                "min_products": 1,
                "max_products": 8,
                "show_lot": False,
                "show_peremption": False,
            },
            "dossier_administratif": {
                "label": "Dossier Administratif",
                "description": "Dossier formel et administratif",
                "header_color": "#214d42",
                "accent_color": "#62a38f",
                "page_bg": "#eef5f1",
                "table_head_bg": "#d9ebe2",
                "border_style": "solid",
                "logo_type": "admin_badge",
                "min_products": 3,
                "max_products": 12,
                "show_lot": False,
                "show_peremption": True,
            },
        }
    )

    # Product family prefixes by category
    product_families: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "pharma_distrib": [
                "Cardio", "Anti-infect", "Neuro", "Gastro", "Pneumo", "Immuno",
                "Derma", "Ortho", "Ophthalmo", "ORL", "Générique", "Spécialité"
            ],
            "facture_premium": [
                "Premium Cardio", "Excellence Pharma", "Prestige Neuro", "Select Derma",
                "Premium Gastro", "Elite Bio", "Luxury Immuno", "Premium ORL"
            ],
            "ticket_compact": [
                "Gen", "Std", "Phar", "Med", "Clin", "Rx", "Pharm", "Lab"
            ],
            "dossier_administratif": [
                "Classe I", "Classe II", "Classe III", "Stupéfiants", "PSM",
                "Biologique", "Référencé", "Remboursable", "Génériqué"
            ],
        }
    )

    font_families: List[str] = field(
        default_factory=lambda: [
            "Arial, sans-serif",
            "Calibri, sans-serif",
            "Verdana, sans-serif",
            "Tahoma, sans-serif",
            "Trebuchet MS, sans-serif",
            "Times New Roman, serif",
            "Georgia, serif",
            "Courier New, monospace",
        ]
    )

    canvas_sizes: List[Dict[str, int]] = field(
        default_factory=lambda: [
            {"width": 1800, "height": 2300},
            {"width": 1700, "height": 2200},
            {"width": 1600, "height": 2100},
        ]
    )

    rotation_range_deg: float = 7.0
    blur_radius_max: float = 1.8
    brightness_range: tuple = (0.82, 1.18)

    missing_cell_probability: float = 0.08
    merged_row_probability: float = 0.12
    misalign_probability: float = 0.25
    handwritten_noise_probability: float = 0.42
    stamp_probability: float = 0.5
    signature_probability: float = 0.4

    augmentation_min_ops: int = 2
    augmentation_max_ops: int = 5

    currency: str = "MAD"
    hard_case_rate: float = 0.12
    error_item_rate: float = 0.12
    ocr_confusion_rate: float = 0.16
    product_category_mix: Dict[str, float] = field(
        default_factory=lambda: {"medicament": 0.65, "parapharmacie": 0.20, "cosmetique_premium": 0.15}
    )


def ensure_output_dirs(cfg: DatasetConfig) -> None:
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.images_dir.mkdir(parents=True, exist_ok=True)
    cfg.annotations_dir.mkdir(parents=True, exist_ok=True)
    cfg.temp_html_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class DatasetV2Config:
    # base
    project_root: Path = Path(__file__).resolve().parent
    user_home: Path = Path.home()
    data_dir: Path = project_root / "data"
    output_dir: Path = project_root / "dataset_v2"
    templates_dir: Path = project_root / "templates"

    # derived folders
    images_dir: Path = output_dir / "images"
    annotations_dir: Path = output_dir / "annotations"
    html_dir: Path = output_dir / "_html"
    reports_dir: Path = output_dir / "reports"
    previews_dir: Path = output_dir / "previews"
    metadata_dir: Path = output_dir / "metadata"

    # dataset sizing and split
    num_documents: int = 1000
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    random_seed: int = 42
    apply_augmentation: bool = True

    suppliers_csv_path: Path = data_dir / "suppliers.csv"
    suppliers_csv_fallbacks: List[Path] = field(
        default_factory=lambda: [
            Path.home() / "Desktop" / "suppliers_202604231724.csv",
            Path.home() / "suppliers_202604231722.csv",
            Path.home() / "Desktop" / "suppliers.csv",
        ]
    )
    medicines_file_candidates: List[Path] = field(
        default_factory=lambda: [
            Path(__file__).resolve().parent / "data" / "wellys_db.xlsx",
            Path.home() / "Downloads" / "wellys_db.xlsx",
            Path(__file__).resolve().parent / "data" / "medicines.csv",
            Path(__file__).resolve().parent / "data" / "medicaments.csv",
        ]
    )

    min_products_per_doc: int = 1
    max_products_per_doc: int = 15

    # item count distribution (percentages)
    distribution_small: float = 0.40  # 3-6
    distribution_medium: float = 0.40  # 7-12
    distribution_large: float = 0.15  # 13-20
    distribution_hard: float = 0.05  # 21-30
    max_items_per_bl: int = 30

    # presence rates
    presence_rate_lot: float = 0.60
    presence_rate_expiry: float = 0.65

    # quantities
    integer_quantity_rate: float = 0.85
    decimal_quantity_rate: float = 0.15

    # shared render settings
    image_format: str = "png"
    image_quality: int = 95
    font_families: List[str] = field(
        default_factory=lambda: [
            "Arial, sans-serif",
            "Calibri, sans-serif",
            "Verdana, sans-serif",
            "Tahoma, sans-serif",
            "Trebuchet MS, sans-serif",
            "Times New Roman, serif",
            "Georgia, serif",
            "Courier New, monospace",
        ]
    )
    canvas_sizes: List[Dict[str, int]] = field(
        default_factory=lambda: [
            {"width": 1800, "height": 2300},
            {"width": 1700, "height": 2200},
            {"width": 1600, "height": 2100},
        ]
    )
    stamp_probability: float = 0.5
    signature_probability: float = 0.4
    augmentation_min_ops: int = 2
    augmentation_max_ops: int = 5
    currency: str = "MAD"
    hard_case_rate: float = 0.12
    error_item_rate: float = 0.12
    ocr_confusion_rate: float = 0.16
    product_category_mix: Dict[str, float] = field(
        default_factory=lambda: {"medicament": 0.65, "parapharmacie": 0.20, "cosmetique_premium": 0.15}
    )

    missing_cell_probability: float = 0.08
    merged_row_probability: float = 0.12
    misalign_probability: float = 0.25
    handwritten_noise_probability: float = 0.42

    # augmentation and difficulty breakdown
    augmentation_rate: float = 0.75
    difficulty_breakdown: Dict[str, float] = field(
        default_factory=lambda: {"easy": 0.5, "medium": 0.35, "hard": 0.15}
    )

    # supplier/template distributions (optional weights)
    supplier_distribution: Optional[Dict[str, float]] = None
    template_distribution: Optional[Dict[str, float]] = None

    # price bands (MAD)
    price_bands: Dict[str, Tuple[float, float]] = field(
        default_factory=lambda: {
            "medicament": (5.0, 300.0),
            "parapharmacie": (20.0, 800.0),
            "cosmetique_premium": (80.0, 1500.0),
        }
    )

    # lot/expiry formats and generation params
    expiry_min_months: int = 6
    expiry_max_months: int = 36
    expiry_formats: List[str] = field(default_factory=lambda: ["%m/%y", "%m/%Y", "%d/%m/%Y"])  # prefer first two

    # preview / report sampling
    previews_count: int = 20
    previews_by_difficulty: Dict[str, int] = field(default_factory=lambda: {"easy": 5, "medium": 5, "hard": 5, "mixed_missing": 5})

    # logging / reproducibility
    verbose: bool = True

    def validate(self) -> None:
        total = self.train_ratio + self.val_ratio + self.test_ratio
        if abs(total - 1.0) > 1e-6:
            raise ValueError("train_ratio + val_ratio + test_ratio must equal 1.0")
        if self.max_items_per_bl < 1:
            raise ValueError("max_items_per_bl must be positive")
        if not 0.0 <= self.presence_rate_lot <= 1.0:
            raise ValueError("presence_rate_lot must be between 0 and 1")
        if not 0.0 <= self.presence_rate_expiry <= 1.0:
            raise ValueError("presence_rate_expiry must be between 0 and 1")
        if not 0.0 <= self.augmentation_rate <= 1.0:
            raise ValueError("augmentation_rate must be between 0 and 1")
        if not 0.0 <= self.hard_case_rate <= 1.0:
            raise ValueError("hard_case_rate must be between 0 and 1")
        if not 0.0 <= self.error_item_rate <= 1.0:
            raise ValueError("error_item_rate must be between 0 and 1")
        if not 0.0 <= self.ocr_confusion_rate <= 1.0:
            raise ValueError("ocr_confusion_rate must be between 0 and 1")


def make_dataset_v2_paths(cfg: DatasetV2Config) -> None:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    for base in [cfg.images_dir, cfg.annotations_dir, cfg.html_dir, cfg.metadata_dir]:
        base.mkdir(parents=True, exist_ok=True)
    for split in ["train", "val", "test"]:
        (cfg.images_dir / split).mkdir(parents=True, exist_ok=True)
        (cfg.annotations_dir / split).mkdir(parents=True, exist_ok=True)


def ensure_dataset_v2_dirs(cfg: DatasetV2Config) -> None:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.images_dir.mkdir(parents=True, exist_ok=True)
    (cfg.images_dir / "train").mkdir(parents=True, exist_ok=True)
    (cfg.images_dir / "val").mkdir(parents=True, exist_ok=True)
    (cfg.images_dir / "test").mkdir(parents=True, exist_ok=True)

    cfg.annotations_dir.mkdir(parents=True, exist_ok=True)
    (cfg.annotations_dir / "train").mkdir(parents=True, exist_ok=True)
    (cfg.annotations_dir / "val").mkdir(parents=True, exist_ok=True)
    (cfg.annotations_dir / "test").mkdir(parents=True, exist_ok=True)

    cfg.html_dir.mkdir(parents=True, exist_ok=True)
    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    cfg.previews_dir.mkdir(parents=True, exist_ok=True)
    cfg.metadata_dir.mkdir(parents=True, exist_ok=True)
