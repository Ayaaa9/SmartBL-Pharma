import json
import time
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from augmentations import AugmentationConfig, DocumentAugmentor
from config import DatasetConfig


class BLRenderer:
    def __init__(self, cfg: DatasetConfig) -> None:
        self.cfg = cfg
        self.env = Environment(
            loader=FileSystemLoader(str(cfg.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.augmentor = DocumentAugmentor(
            seed=cfg.random_seed + 999,
            cfg=AugmentationConfig(
                min_ops=cfg.augmentation_min_ops,
                max_ops=cfg.augmentation_max_ops,
            ),
        )
        # Configuration for browser resource management
        self.browser_recycle_interval = 500  # Recycle browser every 500 docs
        self.screenshot_timeout_ms = 60000  # 60 seconds timeout
        self.max_retries = 3  # Retry failed screenshots up to 3 times

    def render_document(self, browser, payload: Dict[str, Any], retry_count: int = 0) -> bool:
        """
        Render a single document with retry logic.
        Returns True if successful, False if failed after retries.
        """
        template_name = payload["template"]
        context = payload["render_context"]
        annotation = payload["annotation"]
        split = payload.get("split", "train")

        try:
            html = self.env.get_template(template_name).render(**context)

            # Create split-specific directories
            split_images_dir = self.cfg.images_dir / split
            split_annotations_dir = self.cfg.annotations_dir / split
            split_images_dir.mkdir(parents=True, exist_ok=True)
            split_annotations_dir.mkdir(parents=True, exist_ok=True)

            final_file = split_images_dir / f"{payload['doc_id']}.{self.cfg.image_format}"
            json_file = split_annotations_dir / f"{payload['doc_id']}.json"

            page = browser.new_page(
                viewport={
                    "width": context["canvas_width"],
                    "height": context["canvas_height"],
                }
            )
            try:
                page.set_content(html, wait_until="networkidle")
                page.screenshot(
                    path=str(final_file), 
                    full_page=True,
                    timeout=self.screenshot_timeout_ms
                )
            finally:
                page.close()

            if self.cfg.apply_augmentation:
                ops = self.augmentor.augment_file(final_file, difficulty=context.get("difficulty", "medium"))
                annotation["applied_augmentations"] = ops
            else:
                annotation["applied_augmentations"] = []

            with json_file.open("w", encoding="utf-8") as f:
                json.dump(annotation, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            # Retry logic
            if retry_count < self.max_retries:
                print(f"  ⚠️  Erreur {retry_count + 1}/{self.max_retries} pour {payload['doc_id']}: {str(e)[:80]}")
                time.sleep(1)  # Brief pause before retry
                return self.render_document(browser, payload, retry_count + 1)
            else:
                print(f"  ❌ Échec final pour {payload['doc_id']}: {str(e)[:100]}")
                annotation["render_error"] = str(e)[:200]
                json_file = self.cfg.annotations_dir / payload.get("split", "train") / f"{payload['doc_id']}.json"
                json_file.parent.mkdir(parents=True, exist_ok=True)
                with json_file.open("w", encoding="utf-8") as f:
                    json.dump(annotation, f, ensure_ascii=False, indent=2)
                return False

    def render_many(self, documents) -> None:
        """
        Render many documents with browser resource management.
        Recycles browser every N documents to prevent memory buildup.
        """
        with sync_playwright() as p:
            doc_count = 0
            successful = 0
            failed = 0
            browser = None
            
            try:
                for payload in documents:
                    # Recycle browser every N documents to free resources
                    if doc_count % self.browser_recycle_interval == 0:
                        if browser is not None:
                            browser.close()
                            time.sleep(0.5)  # Brief pause between browser instances
                        browser = p.chromium.launch()
                    
                    # Render document
                    success = self.render_document(browser, payload)
                    doc_count += 1
                    
                    if success:
                        successful += 1
                    else:
                        failed += 1
                    
                    # Progress indicator every 50 docs
                    if doc_count % 50 == 0:
                        print(f"  ✓ {successful} rendered, {failed} skipped")
            
            finally:
                if browser is not None:
                    browser.close()
            
            # Summary
            total = successful + failed
            success_rate = (successful / total * 100) if total > 0 else 0
            print(f"\n📊 Rendu complété: {successful}/{total} ({success_rate:.1f}%) documents générés")
