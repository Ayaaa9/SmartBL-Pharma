from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List

import albumentations as A
import cv2
import numpy as np


@dataclass
class AugmentationConfig:
    min_ops: int = 2
    max_ops: int = 5
    easy_min_ops: int = 0
    easy_max_ops: int = 2
    medium_min_ops: int = 2
    medium_max_ops: int = 4
    hard_min_ops: int = 4
    hard_max_ops: int = 7


class DocumentAugmentor:
    def __init__(self, seed: int = 42, cfg: AugmentationConfig | None = None) -> None:
        self.rng = random.Random(seed)
        self.cfg = cfg or AugmentationConfig()
        self._albumentations_map: Dict[str, Callable[[], A.BasicTransform]] = {
            "rotation": lambda: A.Affine(
                rotate=(-10, 10),
                p=1.0,
            ),
            "perspective": lambda: A.Perspective(scale=(0.04, 0.12), keep_size=True, p=1.0),
            "motion_blur": lambda: A.MotionBlur(blur_limit=(3, 11), p=1.0),
            "gaussian_blur": lambda: A.GaussianBlur(blur_limit=(3, 9), p=1.0),
            "brightness_contrast": lambda: A.RandomBrightnessContrast(
                brightness_limit=(-0.28, 0.28),
                contrast_limit=(-0.35, 0.35),
                p=1.0,
            ),
            "iso_noise": lambda: A.ISONoise(color_shift=(0.01, 0.04), intensity=(0.12, 0.38), p=1.0),
            "jpeg": lambda: A.ImageCompression(quality_lower=30, quality_upper=85, p=1.0),
        }
        self._custom_ops = {
            "shadow": self._shadow_simulation,
            "wrinkles": self._paper_wrinkle,
            "occlusion": self._partial_occlusion,
            "stain": self._coffee_stain,
            "tear": self._paper_tear,
        }
        self.available_ops = list(self._albumentations_map.keys()) + list(self._custom_ops.keys())
        self._ops_by_difficulty = {
            "easy": ["rotation", "brightness_contrast", "jpeg", "gaussian_blur"],
            "medium": ["rotation", "perspective", "motion_blur", "gaussian_blur", "brightness_contrast", "iso_noise", "jpeg", "shadow", "wrinkles", "stain"],
            "hard": ["rotation", "perspective", "motion_blur", "gaussian_blur", "brightness_contrast", "iso_noise", "jpeg", "shadow", "wrinkles", "occlusion", "stain", "tear"],
        }

    def augment_image(self, image: np.ndarray, difficulty: str = "medium") -> tuple[np.ndarray, List[str]]:
        if difficulty == "easy":
            n_ops = self.rng.randint(self.cfg.easy_min_ops, self.cfg.easy_max_ops)
        elif difficulty == "hard":
            n_ops = self.rng.randint(self.cfg.hard_min_ops, self.cfg.hard_max_ops)
        else:
            n_ops = self.rng.randint(self.cfg.medium_min_ops, self.cfg.medium_max_ops)

        pool = self._ops_by_difficulty.get(difficulty, self.available_ops)
        picked = self.rng.sample(pool, k=min(n_ops, len(pool)))

        alb_ops = [self._albumentations_map[name]() for name in picked if name in self._albumentations_map]
        custom_ops = [name for name in picked if name in self._custom_ops]

        out = image.copy()
        if alb_ops:
            out = A.Compose(alb_ops)(image=out)["image"]

        for name in custom_ops:
            out = self._custom_ops[name](out)

        return out, picked

    def augment_file(self, image_path: Path, difficulty: str = "medium") -> List[str]:
        img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError(f"Unable to load image at {image_path}")

        augmented, ops = self.augment_image(img, difficulty=difficulty)
        cv2.imwrite(str(image_path), augmented)
        return ops

    def _shadow_simulation(self, image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        overlay = np.zeros((h, w), dtype=np.float32)

        for _ in range(self.rng.randint(1, 3)):
            x1 = self.rng.randint(0, w - 1)
            y1 = self.rng.randint(0, h - 1)
            x2 = self.rng.randint(0, w - 1)
            y2 = self.rng.randint(0, h - 1)
            thickness = self.rng.randint(max(40, w // 20), max(120, w // 8))
            cv2.line(overlay, (x1, y1), (x2, y2), 1.0, thickness)

        overlay = cv2.GaussianBlur(overlay, (0, 0), sigmaX=35, sigmaY=35)
        intensity = self.rng.uniform(0.12, 0.35)
        mask = 1.0 - np.clip(overlay * intensity, 0.0, 0.6)

        out = image.astype(np.float32)
        for c in range(3):
            out[:, :, c] *= mask

        return np.clip(out, 0, 255).astype(np.uint8)

    def _paper_wrinkle(self, image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        y = np.arange(h, dtype=np.float32)
        x = np.arange(w, dtype=np.float32)
        xx, yy = np.meshgrid(x, y)

        freq = self.rng.uniform(0.01, 0.03)
        amp = self.rng.uniform(1.0, 4.5)
        phase = self.rng.uniform(0.0, 6.28)
        displacement = amp * np.sin(xx * freq + phase)

        map_x = xx + displacement
        map_y = yy
        remapped = cv2.remap(
            image,
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT,
        )

        light = (np.sin((xx * freq * 1.8) + phase) * 8.0).astype(np.float32)
        out = remapped.astype(np.float32)
        out[:, :, 0] = np.clip(out[:, :, 0] + light, 0, 255)
        out[:, :, 1] = np.clip(out[:, :, 1] + light, 0, 255)
        out[:, :, 2] = np.clip(out[:, :, 2] + light, 0, 255)
        return out.astype(np.uint8)

    def _partial_occlusion(self, image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        out = image.copy()
        mode = self.rng.choice(["fold", "finger"])

        if mode == "fold":
            occ_w = self.rng.randint(max(60, w // 12), max(120, w // 6))
            x0 = self.rng.randint(0, max(1, w - occ_w))
            color = self.rng.randint(200, 240)
            cv2.rectangle(out, (x0, 0), (x0 + occ_w, h), (color, color, color), -1)
            out = cv2.GaussianBlur(out, (5, 5), 1.0)
        else:
            radius = self.rng.randint(max(40, min(h, w) // 16), max(90, min(h, w) // 8))
            cx = self.rng.randint(radius, max(radius + 1, w - radius))
            cy = self.rng.randint(radius, max(radius + 1, h - radius))
            skin = (
                self.rng.randint(135, 190),
                self.rng.randint(160, 205),
                self.rng.randint(175, 220),
            )
            cv2.circle(out, (cx, cy), radius, skin, -1)
            cv2.circle(out, (cx, cy), radius, (40, 40, 40), 2)

        return out

    def _coffee_stain(self, image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        out = image.copy().astype(np.float32)
        center_x = self.rng.randint(int(w * 0.2), int(w * 0.8))
        center_y = self.rng.randint(int(h * 0.2), int(h * 0.8))
        radius = self.rng.randint(max(40, w // 15), max(70, w // 10))
        intensity = self.rng.uniform(0.16, 0.32)
        for y in range(max(0, center_y - radius), min(h, center_y + radius)):
            for x in range(max(0, center_x - radius), min(w, center_x + radius)):
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                if dist <= radius:
                    fade = (1.0 - dist / radius) ** 2
                    shade = self.rng.uniform(20, 60) * fade * intensity
                    out[y, x] = np.clip(out[y, x] - shade, 0, 255)
        out = cv2.GaussianBlur(out.astype(np.uint8), (9, 9), sigmaX=5)
        return out.astype(np.uint8)

    def _paper_tear(self, image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        out = image.copy()
        shape_width = self.rng.randint(max(40, w // 12), max(80, w // 8))
        top = self.rng.randint(0, h // 4)
        y_start = self.rng.randint(top, top + h // 5)
        points = []
        x = 0
        while x < w:
            jitter_x = self.rng.randint(20, 55)
            jitter_y = self.rng.randint(-15, 15)
            points.append((min(w, x), min(h, max(0, y_start + jitter_y))))
            x += jitter_x
        if points[-1][0] != w:
            points[-1] = (w, points[-1][1])
        cv2.fillPoly(out, [np.array(points, dtype=np.int32)], (245, 245, 245))
        out = cv2.blur(out, (5, 5))
        return out
