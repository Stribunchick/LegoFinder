import json
from pathlib import Path

import cv2
import numpy as np

from new_pipeline.preprocessing import extract_object_mask, crop_by_mask, compute_hsv_hist, safe_gray


class TemplateManager:
    def __init__(self, storage_dir="data/templates"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.orb = cv2.ORB_create(
            nfeatures=1800,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=15,
            patchSize=31,
            fastThreshold=10
        )

    def add_template(self, name, image_bgr):
        if image_bgr is None:
            raise ValueError("Пустое изображение")

        mask = extract_object_mask(image_bgr)
        if mask is None:
            raise ValueError(
                "Не удалось выделить объект. Убедись, что деталь снята на однотонном фоне."
            )

        crop, crop_mask, _ = crop_by_mask(image_bgr, mask, padding=8)
        if crop is None:
            raise ValueError("Не удалось вырезать объект")

        gray = safe_gray(crop)
        keypoints, descriptors = self.orb.detectAndCompute(gray, crop_mask)

        if descriptors is None or len(keypoints) < 15:
            raise ValueError(
                "Слишком мало признаков у детали. Попробуй другое фото, лучше свет или другой ракурс."
            )

        hist = compute_hsv_hist(crop, crop_mask)

        item_dir = self.storage_dir / self._safe_name(name)
        item_dir.mkdir(parents=True, exist_ok=True)

        cv2.imwrite(str(item_dir / "template.png"), crop)
        cv2.imwrite(str(item_dir / "mask.png"), crop_mask)
        np.save(str(item_dir / "descriptors.npy"), descriptors)
        np.save(str(item_dir / "hist.npy"), hist)

        kp_data = []
        for kp in keypoints:
            kp_data.append({
                "x": float(kp.pt[0]),
                "y": float(kp.pt[1]),
                "size": float(kp.size),
                "angle": float(kp.angle),
                "response": float(kp.response),
                "octave": int(kp.octave),
                "class_id": int(kp.class_id),
            })

        meta = {
            "name": name,
            "width": int(crop.shape[1]),
            "height": int(crop.shape[0]),
            "keypoints": kp_data,
        }

        with open(item_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return str(item_dir)

    def list_templates(self):
        result = []
        for item in self.storage_dir.iterdir():
            if not item.is_dir():
                continue
            meta_path = item / "meta.json"
            if not meta_path.exists():
                continue

            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                result.append(meta["name"])
            except Exception:
                continue

        return sorted(result)

    def load_template(self, name):
        item_dir = self.storage_dir / self._safe_name(name)
        meta_path = item_dir / "meta.json"

        if not meta_path.exists():
            raise FileNotFoundError(f"Шаблон '{name}' не найден")

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        image = cv2.imread(str(item_dir / "template.png"))
        mask = cv2.imread(str(item_dir / "mask.png"), cv2.IMREAD_GRAYSCALE)
        descriptors = np.load(str(item_dir / "descriptors.npy"))
        hist = np.load(str(item_dir / "hist.npy"))

        keypoints = []
        for k in meta["keypoints"]:
            kp = cv2.KeyPoint(
                x=float(k["x"]),
                y=float(k["y"]),
                size=float(k["size"]),
                angle=float(k["angle"]),
                response=float(k["response"]),
                octave=int(k["octave"]),
                class_id=int(k["class_id"]),
            )
            keypoints.append(kp)

        return {
            "name": meta["name"],
            "image": image,
            "mask": mask,
            "descriptors": descriptors,
            "hist": hist,
            "keypoints": keypoints,
            "width": int(meta["width"]),
            "height": int(meta["height"]),
        }

    def delete_template(self, name):
        item_dir = self.storage_dir / self._safe_name(name)
        if not item_dir.exists():
            return False

        for file in item_dir.iterdir():
            file.unlink()
        item_dir.rmdir()
        return True

    @staticmethod
    def _safe_name(name):
        clean = "".join(ch if ch.isalnum() or ch in ("_", "-", " ") else "_" for ch in name)
        return clean.strip().replace(" ", "_")