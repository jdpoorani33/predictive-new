import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional
from .config import VisualConfig
from .preprocessing import load_image, preprocess_image, align_components

def compute_ssim_pure(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Computes Structural Similarity Index (SSIM) between two grayscale images of identical shape.
    SSIM range: -1.0 to 1.0 (1.0 = identical).
    """
    if img1 is None or img2 is None or img1.shape != img2.shape:
        return 0.0

    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)

    mu1 = cv2.GaussianBlur(img1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(img2, (11, 11), 1.5)

    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.GaussianBlur(img1 ** 2, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(img2 ** 2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(img1 * img2, (11, 11), 1.5) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return float(np.mean(ssim_map))

class ReferenceComparator:
    """
    Gold Reference Comparison Engine.
    Compares current machine/component image against verified healthy Gold Reference baseline.
    """

    def compare(
        self,
        gold_input: Any,
        current_input: Any,
        align_first: bool = True
    ) -> Dict[str, Any]:
        """
        Executes robust multi-metric comparison between Gold Reference and Current Image.
        Returns detailed metric breakdown, overall similarity score (0-100%), and difference map.
        """
        gold_raw = load_image(gold_input)
        curr_raw = load_image(current_input)

        if gold_raw is None or curr_raw is None:
            return {
                "similarity_score": 0.0,
                "ssim_score": 0.0,
                "feature_match_score": 0.0,
                "edge_similarity_score": 0.0,
                "histogram_similarity": 0.0,
                "has_significant_deviation": True,
                "difference_map": None,
                "status": "COMPARISON_FAILED",
                "reason": "Gold reference or current image is missing/unreadable"
            }

        # 1. Preprocess & Normalize size
        h, w = gold_raw.shape[:2]
        gold_proc = preprocess_image(gold_raw, target_size=(w, h))
        curr_proc = preprocess_image(curr_raw, target_size=(w, h))

        # 2. Alignment via ORB + Homography
        if align_first:
            aligned_curr, align_success, align_ratio = align_components(gold_proc, curr_proc)
        else:
            aligned_curr = curr_proc
            align_success = False
            align_ratio = 1.0

        # Grayscale conversions for spatial analysis
        gray_gold = cv2.cvtColor(gold_proc, cv2.COLOR_BGR2GRAY)
        gray_curr = cv2.cvtColor(aligned_curr, cv2.COLOR_BGR2GRAY)

        # 3. SSIM Metric
        raw_ssim = compute_ssim_pure(gray_gold, gray_curr)
        ssim_score = max(0.0, min(100.0, (raw_ssim + 1.0) / 2.0 * 100.0))  # Normalize [-1, 1] to [0, 100]

        # 4. Feature Matching Score (ORB Keypoint Distance)
        orb = cv2.ORB_create(nfeatures=500)
        kp1, des1 = orb.detectAndCompute(gray_gold, None)
        kp2, des2 = orb.detectAndCompute(gray_curr, None)

        feature_score = 50.0
        if des1 is not None and des2 is not None and len(kp1) > 0 and len(kp2) > 0:
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = matcher.match(des1, des2)
            if matches:
                good_dist = [m.distance for m in matches if m.distance < 64]
                match_ratio = len(good_dist) / float(max(len(kp1), len(kp2)))
                feature_score = min(100.0, match_ratio * 250.0)

        # 5. Canny Edge Structure Comparison
        edges_gold = cv2.Canny(gray_gold, 50, 150)
        edges_curr = cv2.Canny(gray_curr, 50, 150)
        edge_diff = cv2.absdiff(edges_gold, edges_curr)
        edge_similarity = max(0.0, 100.0 - (np.mean(edge_diff) / 255.0 * 200.0))

        # 6. Color / Texture Histogram Similarity (Bhattacharyya Distance)
        hist_gold = cv2.calcHist([gold_proc], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist_curr = cv2.calcHist([aligned_curr], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        cv2.normalize(hist_gold, hist_gold)
        cv2.normalize(hist_curr, hist_curr)
        bhattacharyya = cv2.compareHist(hist_gold, hist_curr, cv2.HISTCMP_BHATTACHARYYA)
        hist_similarity = max(0.0, (1.0 - bhattacharyya) * 100.0)

        # 7. Spatial Difference Map & Heatmap Generation
        diff_raw = cv2.absdiff(gold_proc, aligned_curr)
        diff_gray = cv2.cvtColor(diff_raw, cv2.COLOR_BGR2GRAY)
        diff_blur = cv2.GaussianBlur(diff_gray, (15, 15), 0)
        
        # Apply JET colormap for defect heat map visualization
        diff_heatmap = cv2.applyColorMap(diff_blur, cv2.COLORMAP_JET)
        
        # Overlay heatmap on current image
        diff_overlay = cv2.addWeighted(aligned_curr, 0.65, diff_heatmap, 0.35, 0)

        # Combined Similarity Score Calculation
        overall_similarity = (
            VisualConfig.SSIM_WEIGHT * ssim_score +
            VisualConfig.FEATURE_MATCH_WEIGHT * feature_score +
            VisualConfig.EDGE_DIFF_WEIGHT * edge_similarity
        )
        overall_similarity = max(0.0, min(100.0, overall_similarity))

        has_significant_deviation = overall_similarity < VisualConfig.SIMILARITY_HEALTHY

        return {
            "similarity_score": round(overall_similarity, 1),
            "ssim_score": round(ssim_score, 1),
            "feature_match_score": round(feature_score, 1),
            "edge_similarity_score": round(edge_similarity, 1),
            "histogram_similarity": round(hist_similarity, 1),
            "has_significant_deviation": has_significant_deviation,
            "alignment_applied": align_success,
            "alignment_ratio": round(align_ratio, 2),
            "difference_map_overlay": diff_overlay,
            "status": "SUCCESS"
        }
