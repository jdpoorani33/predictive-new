import cv2
import numpy as np
import base64
from typing import Dict, Any, List, Optional, Union
from .preprocessing import load_image

def draw_detections(
    image_input: Any,
    detections: List[Dict[str, Any]],
    title: Optional[str] = None
) -> np.ndarray:
    """
    Annotates an image with bounding boxes, class labels, confidence scores, and severity colors.
    """
    img = load_image(image_input)
    if img is None:
        return np.zeros((640, 640, 3), dtype=np.uint8)

    annotated = img.copy()

    # Color palette per severity
    colors = {
        "low": (0, 255, 255),      # Yellow
        "medium": (0, 165, 255),   # Orange
        "high": (0, 0, 255),       # Red
        "critical": (0, 0, 255),   # Bright Red
        "none": (0, 255, 0)        # Green
    }

    for d in detections:
        bbox = d.get("bbox", [])
        if len(bbox) != 4:
            continue
        x1, y1, x2, y2 = [int(v) for v in bbox]
        c_name = d.get("class", "defect").upper()
        conf = d.get("confidence", 0.0)
        sev = d.get("severity", "medium").lower()

        color = colors.get(sev, (0, 0, 255))

        # Draw Bounding Box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Label background pill
        label_text = f"{c_name} {int(conf * 100)}%"
        (t_w, t_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

        cv2.rectangle(annotated, (x1, max(0, y1 - 22)), (x1 + t_w + 10, max(22, y1)), color, -1)
        cv2.putText(annotated, label_text, (x1 + 5, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    if title:
        cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 35), (20, 20, 20), -1)
        cv2.putText(annotated, title, (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

    return annotated

def image_to_base64(img: np.ndarray, format_ext: str = ".jpg") -> str:
    """Converts a numpy image array to base64 data URL string."""
    if img is None or img.size == 0:
        return ""
    success, buffer = cv2.imencode(format_ext, img)
    if not success:
        return ""
    encoded = base64.b64encode(buffer).decode("utf-8")
    mime = "image/png" if format_ext.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{encoded}"

def create_side_by_side_comparison(
    gold_img: np.ndarray,
    current_annotated: np.ndarray,
    diff_overlay: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Creates a combined dashboard comparison image:
    [ Gold Reference ] | [ Current Image + YOLO BBoxes ] | [ Difference Map ]
    """
    if gold_img is None:
        gold_img = np.zeros_like(current_annotated)

    h, w = current_annotated.shape[:2]
    gold_resized = cv2.resize(gold_img, (w, h))

    # Add header titles
    g_title = draw_detections(gold_resized, [], title="GOLD REFERENCE (HEALTHY BASELINE)")
    c_title = draw_detections(current_annotated, [], title="CURRENT IMAGE (YOLO11 DETECTED)")

    panels = [g_title, c_title]

    if diff_overlay is not None:
        diff_resized = cv2.resize(diff_overlay, (w, h))
        d_title = draw_detections(diff_resized, [], title="PHYSICAL DIFFERENCE HEATMAP")
        panels.append(d_title)

    combined = np.hstack(panels)
    return combined
