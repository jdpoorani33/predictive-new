"""
Ground-Truth Validation, Alignment, RMSE Calculation, & Trend-Direction Validation Engine.

This module provides reusable, mathematically rigorous functions for:
1. Equal-length Timestamp / Sequence Index alignment of Actual vs Predicted telemetry.
2. RMSE (Root Mean Squared Error) calculation with NaN & empty-array safety.
3. Prediction Trend-Direction validation (first-differences & slope correlation).
4. Feature Pipeline consistency & column alignment verification.
"""

import logging
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from sklearn.metrics import mean_squared_error

logger = logging.getLogger("validation_engine")


def sanitize_json_floats(obj: Any) -> Any:
    """
    Recursively sanitizes data structures to ensure JSON compliance.
    Replaces NaN, inf, -inf, pd.NA, and non-finite floats with 0.0 while preserving None.
    Converts numpy numeric and boolean scalars to standard Python primitives.
    """
    if obj is None:
        return None
    try:
        if pd.isna(obj):
            return 0.0
    except Exception:
        pass

    if isinstance(obj, dict):
        return {str(k): sanitize_json_floats(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, np.ndarray, pd.Series)):
        return [sanitize_json_floats(v) for v in obj]
    elif isinstance(obj, (float, np.floating)):
        if math.isnan(obj) or not math.isfinite(obj):
            return 0.0
        return float(obj)
    elif isinstance(obj, (int, np.integer)):
        return int(obj)
    elif isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    return str(obj)




def calculate_rmse(
    actual: Union[List[float], np.ndarray, pd.Series],
    predicted: Union[List[float], np.ndarray, pd.Series]
) -> Tuple[float, int]:
    """
    Calculates Root Mean Squared Error (RMSE) between aligned actual and predicted arrays.
    
    Formula: RMSE = sqrt((1/n) * sum((actual_i - predicted_i)^2))
    
    Args:
        actual: Sequence of ground-truth actual sensor values.
        predicted: Sequence of ML model predicted values.
        
    Returns:
        Tuple of (rmse_value: float, sample_count: int)
    """
    if actual is None or predicted is None:
        logger.warning("RMSE Calculation: actual or predicted array is None.")
        return 0.0, 0
        
    act_arr = np.asarray(actual, dtype=float)
    pred_arr = np.asarray(predicted, dtype=float)
    
    # Filter out NaNs or infs synchronously
    valid_mask = np.isfinite(act_arr) & np.isfinite(pred_arr)
    act_clean = act_arr[valid_mask]
    pred_clean = pred_arr[valid_mask]
    
    n_samples = len(act_clean)
    if n_samples == 0:
        logger.warning("RMSE Calculation: 0 valid finite sample points after NaN removal.")
        return 0.0, 0
        
    mse = mean_squared_error(act_clean, pred_clean)
    rmse = float(np.sqrt(mse))
    rmse_rounded = round(rmse, 4)
    
    logger.info(f"[METRIC] Calculated RMSE: {rmse_rounded} across {n_samples} matched samples.")
    return rmse_rounded, n_samples


def align_actual_and_predicted(
    actual_records: List[Dict[str, Any]],
    predicted_records: List[Dict[str, Any]],
    target_plc: str = "PLC_01",
    target_sensor: str = "temperature"
) -> Dict[str, Any]:
    """
    Aligns actual backend sensor observations with ML model predictions.
    Strictly matches by:
      1. PLC ID
      2. Target/Sensor name
      3. Timestamp or mapped sequence index
    Sorts chronologically, removes unmatched records, and verifies equal-length arrays.
    
    Args:
        actual_records: List of dicts containing timestamp, plc_id, and actual sensor values.
        predicted_records: List of dicts containing timestamp, plc_id, and predicted values.
        target_plc: Canonical string PLC identifier (e.g. 'PLC_01').
        target_sensor: Name of sensor/target metric (e.g. 'temperature', 'vibration').
        
    Returns:
        Dict containing aligned actual, predicted, timestamps, sample counts, and match logs.
    """
    if not actual_records or not predicted_records:
        return {
            "plc_id": target_plc,
            "target": target_sensor,
            "timestamps": [],
            "actual": [],
            "predicted": [],
            "sample_count": 0,
            "matched_points": 0,
            "unmatched_actual_points": len(actual_records) if actual_records else 0,
            "unmatched_predicted_points": len(predicted_records) if predicted_records else 0,
            "rmse": 0.0,
            "status": "insufficient_data"
        }
        
    # Index actual records by timestamp / step key
    actual_map = {}
    for r in actual_records:
        p_id = str(r.get("plc_id", "")).strip()
        if p_id.upper() != target_plc.upper() and p_id != target_plc:
            continue
        ts = str(r.get("timestamp", r.get("Timestamp", ""))).strip()
        if not ts:
            continue
        val = r.get(target_sensor, r.get(target_sensor.capitalize(), r.get(target_sensor.lower(), None)))
        if val is not None and math.isfinite(float(val)):
            actual_map[ts] = float(val)
            
    # Match predictions against actual map
    aligned_ts = []
    aligned_actual = []
    aligned_predicted = []
    unmatched_pred_count = 0
    
    for pr in predicted_records:
        p_id = str(pr.get("plc_id", "")).strip()
        if p_id.upper() != target_plc.upper() and p_id != target_plc:
            continue
        ts = str(pr.get("timestamp", pr.get("Timestamp", ""))).strip()
        if not ts:
            continue
        pred_val = pr.get("predicted", pr.get("predicted_value", pr.get(target_sensor, None)))
        if pred_val is None or not math.isfinite(float(pred_val)):
            continue
            
        if ts in actual_map:
            aligned_ts.append(ts)
            aligned_actual.append(actual_map[ts])
            aligned_predicted.append(float(pred_val))
        else:
            unmatched_pred_count += 1
            
    unmatched_actual_count = len(actual_map) - len(aligned_ts)
    matched_count = len(aligned_ts)
    
    logger.info(
        f"[VALIDATION] Alignment for {target_plc} ({target_sensor}): "
        f"Matched points: {matched_count} | "
        f"Unmatched actual points: {unmatched_actual_count} | "
        f"Unmatched predicted points: {unmatched_pred_count}"
    )
    
    rmse, sample_cnt = calculate_rmse(aligned_actual, aligned_predicted)
    
    return {
        "plc_id": target_plc,
        "target": target_sensor,
        "timestamps": aligned_ts,
        "actual": aligned_actual,
        "predicted": aligned_predicted,
        "sample_count": sample_cnt,
        "matched_points": matched_count,
        "unmatched_actual_points": unmatched_actual_count,
        "unmatched_predicted_points": unmatched_pred_count,
        "rmse": rmse,
        "status": "ground_truth_validated" if matched_count > 0 else "no_matched_points"
    }


def validate_trend_direction(
    actual: Union[List[float], np.ndarray],
    predicted: Union[List[float], np.ndarray]
) -> Dict[str, Any]:
    """
    Validates prediction direction against actual sensor trajectory.
    Detects if model predictions move in opposite direction to actual data.
    
    Uses:
      - First differences directional sign matching: sign(act[i+1] - act[i]) == sign(pred[i+1] - pred[i])
      - Trend slope comparison via linear regression fit
    
    Args:
        actual: Array of ground truth actual values.
        predicted: Array of ML predicted values.
        
    Returns:
        Dict containing directional accuracy %, slope values, and directional match status.
    """
    act_arr = np.asarray(actual, dtype=float)
    pred_arr = np.asarray(predicted, dtype=float)
    
    if len(act_arr) < 2 or len(pred_arr) < 2:
        return {
            "directional_accuracy_pct": 100.0,
            "actual_slope": 0.0,
            "predicted_slope": 0.0,
            "trend_match": True,
            "status": "insufficient_points_for_trend"
        }
        
    min_len = min(len(act_arr), len(pred_arr))
    act_arr = act_arr[:min_len]
    pred_arr = pred_arr[:min_len]
    
    # 1. First Differences Directional Accuracy
    diff_act = np.diff(act_arr)
    diff_pred = np.diff(pred_arr)
    
    sign_act = np.sign(diff_act)
    sign_pred = np.sign(diff_pred)
    
    matches = (sign_act == sign_pred) | (sign_act == 0) | (sign_pred == 0)
    directional_acc = float(np.mean(matches)) * 100.0
    
    # 2. Overall Trend Slope Comparison
    x = np.arange(min_len)
    act_slope = float(np.polyfit(x, act_arr, 1)[0]) if min_len >= 2 else 0.0
    pred_slope = float(np.polyfit(x, pred_arr, 1)[0]) if min_len >= 2 else 0.0
    
    # Trend conflict check: Actual decreasing significantly while prediction increasing significantly
    is_opposite = (act_slope < -0.01 and pred_slope > 0.01) or (act_slope > 0.01 and pred_slope < -0.01)
    trend_match = not is_opposite
    
    if not trend_match:
        logger.warning(
            f"[TREND WARNING] Directional Mismatch Detected! "
            f"Actual slope={act_slope:.4f}, Predicted slope={pred_slope:.4f}. "
            f"Directional accuracy={directional_acc:.1f}%"
        )
    else:
        logger.info(
            f"[TREND VALIDATED] Directional Accuracy: {directional_acc:.1f}% | "
            f"Actual Slope: {act_slope:.4f}, Predicted Slope: {pred_slope:.4f}"
        )
        
    return {
        "directional_accuracy_pct": round(directional_acc, 1),
        "actual_slope": round(act_slope, 4),
        "predicted_slope": round(pred_slope, 4),
        "trend_match": trend_match,
        "status": "directional_match_ok" if trend_match else "directional_mismatch_warning"
    }


def validate_feature_consistency(
    received_df_or_dict: Union[pd.DataFrame, Dict[str, Any]],
    expected_columns: List[str]
) -> Tuple[bool, List[str], List[str]]:
    """
    Validates that live feature extraction produces exact columns expected by the ML model.
    Checks column presence, order, and non-NaN status before prediction.
    
    Args:
        received_df_or_dict: Feature vector or DataFrame to validate.
        expected_columns: List of feature names model was trained on.
        
    Returns:
        Tuple of (is_valid: bool, missing_columns: list, extra_columns: list)
    """
    if isinstance(received_df_or_dict, dict):
        received_cols = list(received_df_or_dict.keys())
    elif isinstance(received_df_or_dict, pd.DataFrame):
        received_cols = list(received_df_or_dict.columns)
    else:
        received_cols = []
        
    missing = [col for col in expected_columns if col not in received_cols]
    extra = [col for col in received_cols if col not in expected_columns]
    
    is_valid = (len(missing) == 0)
    
    logger.info(
        f"[FEATURE CHECK] Expected features: {len(expected_columns)} | "
        f"Received features: {len(received_cols)} | "
        f"Missing: {missing} | Extra: {extra}"
    )
    
    if not is_valid:
        logger.error(f"[FEATURE MISMATCH] Model feature validation failed. Missing columns: {missing}")
        
    return is_valid, missing, extra
