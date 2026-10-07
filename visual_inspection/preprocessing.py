import cv2
import numpy as np
import os
from typing import Tuple, Dict, Any, Optional, Union
from .config import VisualConfig

def load_image(image_input: Union[str, np.ndarray, bytes]) -> Optional[np.ndarray]:
    """
    Safely loads an image from file path, numpy array, or byte stream.
    Returns BGR numpy array or None if invalid.
    """
    if image_input is None:
        return None
    if isinstance(image_input, np.ndarray):
        return image_input.copy()
    if isinstance(image_input, str):
        if not os.path.exists(image_input) or os.path.getsize(image_input) == 0:
            return None
        img = cv2.imread(image_input)
        return img
    if isinstance(image_input, (bytes, bytearray)):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    return None

def validate_image_quality(img: np.ndarray) -> Dict[str, Any]:
    """
    Evaluates image quality based on:
    - Resolution check
    - Blur score (Laplacian variance)
    - Exposure check (Mean brightness & histogram variance)
    """
    if img is None or img.size == 0:
        return {
            "is_valid": False,
            "quality_status": "POOR",
            "quality_score": 0.0,
            "blur_score": 0.0,
            "exposure_score": 0.0,
            "reasons": ["Image is empty or unreadable"]
        }

    h, w = img.shape[:2]
    reasons = []

    # 1. Resolution Check
    if h < VisualConfig.MIN_RESOLUTION[0] or w < VisualConfig.MIN_RESOLUTION[1]:
        reasons.append(f"Low resolution ({w}x{h} < {VisualConfig.MIN_RESOLUTION[1]}x{VisualConfig.MIN_RESOLUTION[0]})")

    # Convert to grayscale for analysis
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    # 2. Blur Check via Laplacian Variance
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    is_blurry = blur_score < VisualConfig.BLUR_LAPLACIAN_VAR_MIN
    if is_blurry:
        reasons.append(f"Image is blurry (blur score {blur_score:.1f} < {VisualConfig.BLUR_LAPLACIAN_VAR_MIN})")

    # 3. Exposure Check via Mean Brightness
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))
    
    is_underexposed = mean_val < VisualConfig.EXPOSURE_MIN_MEAN
    is_overexposed = mean_val > VisualConfig.EXPOSURE_MAX_MEAN

    if is_underexposed:
        reasons.append(f"Underexposed/Too dark (mean brightness {mean_val:.1f})")
    elif is_overexposed:
        reasons.append(f"Overexposed/Too bright (mean brightness {mean_val:.1f})")

    # Quality Score calculation (0-100)
    blur_pct = min(100.0, (blur_score / (VisualConfig.BLUR_LAPLACIAN_VAR_MIN * 2.5)) * 100.0)
    
    # Exposure penalty
    exp_pct = 100.0
    if is_underexposed:
        exp_pct = max(0.0, (mean_val / VisualConfig.EXPOSURE_MIN_MEAN) * 100.0)
    elif is_overexposed:
        exp_pct = max(0.0, (1.0 - (mean_val - VisualConfig.EXPOSURE_MAX_MEAN) / (255 - VisualConfig.EXPOSURE_MAX_MEAN)) * 100.0)

    quality_score = max(0.0, min(100.0, 0.6 * blur_pct + 0.4 * exp_pct))

    is_valid = len(reasons) == 0 and quality_score >= 40.0
    quality_status = "GOOD" if quality_score >= 75.0 else ("ACCEPTABLE" if is_valid else "POOR")

    return {
        "is_valid": is_valid,
        "quality_status": quality_status,
        "quality_score": round(quality_score, 1),
        "blur_score": round(blur_score, 1),
        "exposure_mean": round(mean_val, 1),
        "contrast_std": round(std_val, 1),
        "reasons": reasons if reasons else ["Image quality is optimal"]
    }

def preprocess_image(img: np.ndarray, target_size: Tuple[int, int] = (640, 640)) -> np.ndarray:
    """
    Standardizes image size, applies noise reduction (Bilateral filter),
    and contrast normalization (CLAHE) while preserving defect edges.
    """
    if img is None:
        return np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)

    # Resize cleanly preserving aspect ratio if possible or standard resizing
    resized = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)

    # Convert to LAB to apply CLAHE on L-channel (preserves color balance)
    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    limg = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    # Subtle noise reduction
    denoised = cv2.bilateralFilter(enhanced, d=5, sigmaColor=35, sigmaSpace=35)
    return denoised

def align_components(
    gold_img: np.ndarray,
    current_img: np.ndarray,
    max_features: int = 1000
) -> Tuple[np.ndarray, bool, float]:
    """
    Aligns current_img to gold_img using ORB feature matching and RANSAC Homography.
    Returns (aligned_current_img, success_flag, alignment_match_ratio).
    """
    if gold_img is None or current_img is None:
        return current_img, False, 0.0

    # Ensure same size before feature detection
    h_gold, w_gold = gold_img.shape[:2]
    curr_resized = cv2.resize(current_img, (w_gold, h_gold), interpolation=cv2.INTER_AREA)

    gray_gold = cv2.cvtColor(gold_img, cv2.COLOR_BGR2GRAY) if len(gold_img.shape) == 3 else gold_img
    gray_curr = cv2.cvtColor(curr_resized, cv2.COLOR_BGR2GRAY) if len(curr_resized.shape) == 3 else curr_resized

    orb = cv2.ORB_create(nfeatures=max_features)
    kp1, des1 = orb.detectAndCompute(gray_gold, None)
    kp2, des2 = orb.detectAndCompute(gray_curr, None)

    if des1 is None or des2 is None or len(kp1) < 8 or len(kp2) < 8:
        return curr_resized, False, 0.0

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)

    # Take top 30% matches
    good_num = int(len(matches) * 0.3)
    good_matches = matches[:max(8, good_num)]

    if len(good_matches) < 4:
        return curr_resized, False, len(good_matches) / max(1, len(kp1))

    pts_gold = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    pts_curr = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    try:
        H, mask = cv2.findHomography(pts_curr, pts_gold, cv2.RANSAC, 5.0)
        if H is None:
            return curr_resized, False, 0.0

        aligned = cv2.warpPerspective(curr_resized, H, (w_gold, h_gold))
        inliers = np.sum(mask)
        match_ratio = min(1.0, float(inliers) / max(1, len(good_matches)))
        return aligned, True, round(match_ratio, 3)
    except Exception:
        return curr_resized, False, 0.0
