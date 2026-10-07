import os
import json
import cv2
from typing import Dict, Any
from .config import VisualConfig

def analyze_dataset(dataset_dir: str = None) -> Dict[str, Any]:
    """
    Analyzes dataset directory structure, class balance, split counts,
    and missing or corrupted files. Generates dataset report.
    """
    target_dir = dataset_dir or VisualConfig.DATASET_DIR

    splits = ["train", "val", "test"]
    report = {
        "dataset_path": target_dir,
        "splits": {},
        "class_counts": {c: {"train": 0, "val": 0, "test": 0, "total": 0} for c in VisualConfig.CLASSES},
        "corrupted_images": [],
        "unlabeled_images": [],
        "total_images": 0,
        "total_annotations": 0
    }

    for split in splits:
        img_dir = os.path.join(target_dir, "images", split)
        lbl_dir = os.path.join(target_dir, "labels", split)

        if not os.path.exists(img_dir):
            report["splits"][split] = {"images": 0, "labels": 0}
            continue

        img_files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        lbl_files = [f for f in os.listdir(lbl_dir) if f.lower().endswith('.txt')] if os.path.exists(lbl_dir) else []

        split_annotations = 0

        for img_name in img_files:
            img_path = os.path.join(img_dir, img_name)
            # Check if valid image
            img = cv2.imread(img_path)
            if img is None:
                report["corrupted_images"].append(img_path)
                continue

            report["total_images"] += 1

            # Corresponding label file
            base_name = os.path.splitext(img_name)[0]
            lbl_path = os.path.join(lbl_dir, f"{base_name}.txt")

            if not os.path.exists(lbl_path):
                report["unlabeled_images"].append(img_path)
                continue

            # Read labels
            try:
                with open(lbl_path, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])
                            if 0 <= cls_id < len(VisualConfig.CLASSES):
                                cls_name = VisualConfig.CLASSES[cls_id]
                                report["class_counts"][cls_name][split] += 1
                                report["class_counts"][cls_name]["total"] += 1
                                split_annotations += 1
                                report["total_annotations"] += 1
            except Exception:
                pass

        report["splits"][split] = {
            "images": len(img_files),
            "labels": len(lbl_files),
            "annotations": split_annotations
        }

    report_path = os.path.join(target_dir, "dataset_report.json")
    try:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
    except Exception:
        pass

    return report
