import os
import cv2
import numpy as np
from typing import Dict, Any, Tuple
from .preprocessing import load_image, validate_image_quality
from .config import VisualConfig

def validate_gold_reference(reference_input: Any) -> Dict[str, Any]:
    """
    Validates a Gold Reference image.
    Requirements for a VALID Gold Reference:
    - Image exists and can be loaded
    - Resolution >= (200, 200)
    - Non-blurry (Laplacian variance > threshold)
    - Good exposure (mean brightness between 20 and 235)
    - Valid contrast (standard deviation > 15.0)

    Returns dict with:
        is_valid: bool
        status: "VALID" | "INVALID"
        quality_info: dict
        reasons: list of strings
    """
    img = load_image(reference_input)
    if img is None:
        return {
            "is_valid": False,
            "status": "INVALID",
            "reasons": ["Gold reference image file missing, corrupted, or unreadable"],
            "quality_info": {}
        }

    quality = validate_image_quality(img)
    reasons = []

    # Extra strict checks for Gold Reference baseline
    h, w = img.shape[:2]
    if h < 200 or w < 200:
        reasons.append(f"Gold reference resolution is too low ({w}x{h})")

    if quality.get("contrast_std", 0.0) < 12.0:
        reasons.append("Gold reference lacks sufficient contrast / detail")

    if not quality["is_valid"]:
        reasons.extend(quality["reasons"])

    is_valid = len(reasons) == 0 and quality["quality_score"] >= 50.0
    status = "VALID" if is_valid else "INVALID"

    return {
        "is_valid": is_valid,
        "status": status,
        "resolution": f"{w}x{h}",
        "quality_score": quality.get("quality_score", 0.0),
        "blur_score": quality.get("blur_score", 0.0),
        "reasons": reasons if reasons else ["Gold reference image verified and healthy"],
        "quality_info": quality
    }
