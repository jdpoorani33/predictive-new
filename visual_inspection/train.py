import os
import yaml
import json
import logging
from ultralytics import YOLO
from .config import VisualConfig
from .dataset_analyzer import analyze_dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("YOLO11_Train")

def prepare_yaml_config(dataset_dir: str) -> str:
    """Generates YOLO dataset config YAML file."""
    yaml_data = {
        "path": os.path.abspath(dataset_dir),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {i: name for i, name in enumerate(VisualConfig.CLASSES)}
    }
    yaml_path = os.path.join(dataset_dir, "dataset.yaml")
    with open(yaml_path, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False)
    return yaml_path

def train_yolo11_model(
    epochs: int = 50,
    img_size: int = 640,
    batch_size: int = 16,
    dataset_dir: Optional[str] = None
) -> str:
    """
    Executes fine-tuning pipeline for YOLO11 on industrial defect dataset.
    Evaluates Precision, Recall, mAP50, mAP50-95, and saves best model weights.
    """
    d_dir = dataset_dir or VisualConfig.DATASET_DIR
    logger.info("=== Analyzing visual dataset quality & class balance ===")
    analysis = analyze_dataset(d_dir)
    logger.info(f"Dataset summary: {analysis['total_images']} total images, {analysis['total_annotations']} annotations across {len(VisualConfig.CLASSES)} classes.")

    if analysis["total_images"] == 0:
        logger.warning("No images found in dataset directory. Model training requires a labeled dataset in YOLO format.")
        return ""

    yaml_path = prepare_yaml_config(d_dir)
    logger.info(f"YOLO dataset configuration saved to {yaml_path}")

    # Load baseline model
    logger.info(f"Initializing YOLO11 baseline checkpoint: {VisualConfig.YOLO_BASE_CHECKPOINT}")
    model = YOLO(VisualConfig.YOLO_BASE_CHECKPOINT)

    # Train model with industrial augmentations
    results = model.train(
        data=yaml_path,
        epochs=epochs,
        imgsz=img_size,
        batch=batch_size,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        scale=0.5,
        project=os.path.join(VisualConfig.BASE_DIR, "runs"),
        name="yolo11_defect_inspection",
        exist_ok=True,
        save=True,
        verbose=True
    )

    # Evaluate model on test set
    metrics = model.val(data=yaml_path, split="val")

    eval_summary = {
        "precision": float(metrics.results_dict.get("metrics/precision(B)", 0.0)),
        "recall": float(metrics.results_dict.get("metrics/recall(B)", 0.0)),
        "mAP50": float(metrics.results_dict.get("metrics/mAP50(B)", 0.0)),
        "mAP50-95": float(metrics.results_dict.get("metrics/mAP50-95(B)", 0.0))
    }

    logger.info(f"Validation Metrics: {eval_summary}")

    # Export best model to visual_inspection/models/best.pt
    best_weights = os.path.join(VisualConfig.BASE_DIR, "runs", "yolo11_defect_inspection", "weights", "best.pt")
    target_weights = VisualConfig.DEFAULT_MODEL_PATH

    os.makedirs(VisualConfig.MODEL_DIR, exist_ok=True)
    if os.path.exists(best_weights):
        import shutil
        shutil.copy(best_weights, target_weights)
        logger.info(f"Fine-tuned YOLO11 weights saved successfully to {target_weights}")
        return target_weights

    return ""

if __name__ == "__main__":
    train_yolo11_model(epochs=10)
