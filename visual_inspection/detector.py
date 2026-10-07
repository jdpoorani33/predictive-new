import os
import cv2
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Union
from ultralytics import YOLO
from .config import VisualConfig
from .preprocessing import load_image

logger = logging.getLogger("uvicorn.error")

class YOLO11Detector:
    """
    YOLO11 Object Detection Engine for Industrial Machine/Component Inspection.
    Detects physical defects (crack, corrosion, leakage, belt_damage, component_damage, overheating, smoke).
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or VisualConfig.DEFAULT_MODEL_PATH
        self.model = None
        self.is_custom = False
        self._initialize_model()

    def _initialize_model(self):
        try:
            if os.path.exists(self.model_path):
                logger.info(f"Loading custom fine-tuned YOLO11 model from {self.model_path}...")
                self.model = YOLO(self.model_path)
                self.is_custom = True
            else:
                logger.info(f"Custom model {self.model_path} not found. Loading pretrained YOLO11 checkpoint ({VisualConfig.YOLO_BASE_CHECKPOINT})...")
                self.model = YOLO(VisualConfig.YOLO_BASE_CHECKPOINT)
                self.is_custom = False
        except Exception as e:
            logger.error(f"Failed to initialize YOLO11 model: {e}. Falling back to default YOLO11n...")
            try:
                self.model = YOLO("yolo11n.pt")
            except Exception as e2:
                logger.error(f"Fallback YOLO model load failed: {e2}")
                self.model = None

    def detect(self, image_input: Any, conf_threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Runs YOLO11 inference on the given image.
        Returns detailed structured detection results.
        """
        conf_thresh = conf_threshold or VisualConfig.CONF_THRESHOLD
        img = load_image(image_input)

        if img is None or self.model is None:
            return {
                "detections": [],
                "count": 0,
                "has_defects": False,
                "highest_confidence": 0.0,
                "max_severity": "none",
                "model_type": "YOLO11" if self.model else "None"
            }

        h, w = img.shape[:2]
        img_area = float(h * w)

        try:
            results = self.model.predict(
                source=img,
                conf=conf_thresh,
                iou=VisualConfig.IOU_THRESHOLD,
                verbose=False
            )

            detections = []
            highest_conf = 0.0
            max_severity_rank = 0

            severity_levels = {0: "none", 1: "low", 2: "medium", 3: "high", 4: "critical"}

            for r in results:
                boxes = r.boxes
                if boxes is None:
                    continue

                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    xyxy = box.xyxy[0].cpu().numpy().tolist()

                    x1, y1, x2, y2 = [float(v) for v in xyxy]
                    box_w = max(0.0, x2 - x1)
                    box_h = max(0.0, y2 - y1)
                    area_px = box_w * box_h
                    area_pct = round((area_px / img_area) * 100.0, 2)

                    # Map class name
                    if hasattr(self.model, "names") and cls_id in self.model.names:
                        raw_class_name = self.model.names[cls_id]
                    else:
                        raw_class_name = VisualConfig.CLASSES[cls_id % len(VisualConfig.CLASSES)]

                    class_name = str(raw_class_name).lower()

                    # Determine severity rank
                    sev_weight = VisualConfig.CLASS_SEVERITY_WEIGHTS.get(class_name, 1.5)
                    sev_score = conf * (area_pct / 10.0 + 1.0) * sev_weight

                    if sev_score > 3.0 or (conf > 0.85 and area_pct > 8.0):
                        sev_rank = 4
                    elif sev_score > 2.0 or (conf > 0.70 and area_pct > 4.0):
                        sev_rank = 3
                    elif sev_score > 1.0:
                        sev_rank = 2
                    else:
                        sev_rank = 1

                    if sev_rank > max_severity_rank:
                        max_severity_rank = sev_rank

                    if conf > highest_conf:
                        highest_conf = conf

                    detections.append({
                        "class": class_name,
                        "confidence": round(conf, 3),
                        "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        "area_pixels": int(area_px),
                        "area_percentage": area_pct,
                        "location": [round((x1 + x2) / 2.0, 1), round((y1 + y2) / 2.0, 1)],
                        "severity": severity_levels[sev_rank]
                    })

            has_defects = len(detections) > 0 and highest_conf >= VisualConfig.CONF_THRESHOLD

            return {
                "detections": detections,
                "count": len(detections),
                "has_defects": has_defects,
                "highest_confidence": round(highest_conf, 3),
                "max_severity": severity_levels[max_severity_rank],
                "is_custom_fine_tuned": self.is_custom,
                "model_type": f"YOLO11 {'Fine-Tuned' if self.is_custom else 'Pretrained'}"
            }

        except Exception as e:
            logger.error(f"Error during YOLO11 inference: {e}", exc_info=True)
            return {
                "detections": [],
                "count": 0,
                "has_defects": False,
                "highest_confidence": 0.0,
                "max_severity": "none",
                "error": str(e)
            }
