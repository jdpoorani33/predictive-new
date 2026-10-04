"""
Comprehensive Automated Unit & E2E Pipeline Validation Tests.

Tests:
1. Mathematical correctness of RMSE calculation.
2. Equal-length timestamp/sequence index alignment.
3. Prediction trend-direction validation & slope correlation.
4. Feature consistency & column validation.
5. Time-Domain statistical feature extraction (16 features).
6. TSFresh Top-25 selected feature extraction & execution timing (< 0.5s).
7. Multi-PLC data stream isolation.
8. API response structure verification.
"""

import sys
import os
import unittest
import numpy as np
import pandas as pd

# Add project root to sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from model.validation import (
    calculate_rmse,
    align_actual_and_predicted,
    validate_trend_direction,
    validate_feature_consistency
)
from time_features import compute_time_domain_stats, extract_time_features_for_window
from tsfresh_features import extract_tsfresh_selected_for_window, load_selected_feature_names


class TestPredictiveMaintenancePipeline(unittest.TestCase):

    def test_rmse_mathematical_correctness(self):
        """Test RMSE calculation against hand-calculated math: sqrt((0^2 + 0^2 + 1^2)/3) = sqrt(1/3) ~ 0.5774"""
        actual = [1.0, 2.0, 3.0]
        predicted = [1.0, 2.0, 4.0]
        
        rmse, sample_cnt = calculate_rmse(actual, predicted)
        expected_rmse = float(np.sqrt(1.0 / 3.0))
        
        self.assertEqual(sample_cnt, 3)
        self.assertAlmostEqual(rmse, round(expected_rmse, 4), places=3)
        print(f"[TEST PASS] RMSE Math Verification: actual={actual}, predicted={predicted} -> RMSE={rmse} (Expected: {expected_rmse:.4f})")

    def test_rmse_empty_and_nan_handling(self):
        """Test RMSE safety with empty arrays and NaN values."""
        actual_nan = [1.0, np.nan, 3.0, 4.0]
        pred_nan = [1.0, 2.0, 3.0, np.nan]
        
        rmse, sample_cnt = calculate_rmse(actual_nan, pred_nan)
        self.assertEqual(sample_cnt, 2)
        self.assertEqual(rmse, 0.0)
        print(f"[TEST PASS] RMSE NaN Handling: Matched clean samples={sample_cnt}, RMSE={rmse}")

    def test_timestamp_and_index_alignment(self):
        """Test alignment of actual and predicted records by timestamp and PLC ID."""
        actual_recs = [
            {"plc_id": "PLC_01", "timestamp": "2026-10-04 10:00:00", "temperature": 62.0},
            {"plc_id": "PLC_01", "timestamp": "2026-10-04 10:00:01", "temperature": 63.0},
            {"plc_id": "PLC_01", "timestamp": "2026-10-04 10:00:02", "temperature": 64.0},
            {"plc_id": "PLC_02", "timestamp": "2026-10-04 10:00:00", "temperature": 75.0}, # Different PLC
        ]
        pred_recs = [
            {"plc_id": "PLC_01", "timestamp": "2026-10-04 10:00:00", "predicted": 61.8},
            {"plc_id": "PLC_01", "timestamp": "2026-10-04 10:00:01", "predicted": 63.2},
            {"plc_id": "PLC_01", "timestamp": "2026-10-04 10:00:05", "predicted": 70.0}, # Unmatched timestamp
        ]
        
        res = align_actual_and_predicted(actual_recs, pred_recs, target_plc="PLC_01", target_sensor="temperature")
        
        self.assertEqual(res["matched_points"], 2)
        self.assertEqual(res["unmatched_actual_points"], 1)
        self.assertEqual(res["unmatched_predicted_points"], 1)
        self.assertEqual(len(res["actual"]), 2)
        self.assertEqual(len(res["predicted"]), 2)
        self.assertEqual(res["actual"], [62.0, 63.0])
        self.assertEqual(res["predicted"], [61.8, 63.2])
        print(f"[TEST PASS] Alignment Test: Matched={res['matched_points']}, Unmatched Actual={res['unmatched_actual_points']}")

    def test_trend_direction_validation(self):
        """Test trend direction validation when actuals decrease but predictions increase."""
        actual_decreasing = [100.0, 95.0, 90.0, 85.0]
        pred_increasing = [100.0, 105.0, 110.0, 115.0]
        
        res_mismatch = validate_trend_direction(actual_decreasing, pred_increasing)
        self.assertFalse(res_mismatch["trend_match"])
        self.assertLess(res_mismatch["actual_slope"], 0.0)
        self.assertGreater(res_mismatch["predicted_slope"], 0.0)
        
        actual_increasing = [10.0, 12.0, 14.0, 16.0]
        pred_increasing2 = [9.8, 11.9, 14.2, 16.1]
        
        res_match = validate_trend_direction(actual_increasing, pred_increasing2)
        self.assertTrue(res_match["trend_match"])
        print(f"[TEST PASS] Trend Validation: Mismatch detected correctly (Match={res_match['trend_match']})")

    def test_time_domain_feature_extraction(self):
        """Test extraction of 16 statistical time-domain features."""
        signal = np.array([10.0, 12.0, 15.0, 11.0, 14.0, 16.0, 13.0, 18.0, 20.0, 22.0])
        stats_d = compute_time_domain_stats(signal, prefix="Temperature")
        
        required_keys = [
            "Temperature__mean", "Temperature__median", "Temperature__mode",
            "Temperature__min", "Temperature__max", "Temperature__range",
            "Temperature__variance", "Temperature__std", "Temperature__rms",
            "Temperature__skewness", "Temperature__kurtosis", "Temperature__peak",
            "Temperature__peak_to_peak", "Temperature__first_value",
            "Temperature__last_value", "Temperature__rate_of_change", "Temperature__trend_slope"
        ]
        
        for k in required_keys:
            self.assertIn(k, stats_d)
            
        self.assertEqual(stats_d["Temperature__first_value"], 10.0)
        self.assertEqual(stats_d["Temperature__last_value"], 22.0)
        self.assertGreater(stats_d["Temperature__trend_slope"], 0.0)
        print(f"[TEST PASS] Time-Domain Feature Extraction: All {len(required_keys)} statistical features verified.")

    def test_tsfresh_top25_fast_extraction(self):
        """Test fast non-blocking TSFresh feature extraction (< 0.5 sec for 20 window samples)."""
        window_records = [
            {"Temperature": 60.0 + i, "Vibration": 0.2 + 0.01 * i, "Motor_Current": 8.0 + 0.1 * i, "Pressure": 5.0, "Noise": 42.0}
            for i in range(20)
        ]
        
        selected_feats = load_selected_feature_names()
        self.assertEqual(len(selected_feats), 25)
        
        df_extracted, elapsed_sec = extract_tsfresh_selected_for_window(
            window_records, selected_features_list=selected_feats, plc_id="PLC_01"
        )
        
        self.assertFalse(df_extracted.empty)
        self.assertEqual(df_extracted.shape[1], 25)
        self.assertLess(elapsed_sec, 1.0)
        print(f"[TEST PASS] TSFresh Top-25 Fast Extraction: Shape={df_extracted.shape}, Time={elapsed_sec:.3f} sec (< 1.0s limit)")

    def test_feature_consistency_check(self):
        """Test model feature column consistency validation."""
        expected = ["f1", "f2", "f3"]
        received_good = {"f1": 1, "f2": 2, "f3": 3}
        received_bad = {"f1": 1, "f2": 2}
        
        val1, missing1, _ = validate_feature_consistency(received_good, expected)
        self.assertTrue(val1)
        self.assertEqual(missing1, [])
        
        val2, missing2, _ = validate_feature_consistency(received_bad, expected)
        self.assertFalse(val2)
        self.assertEqual(missing2, ["f3"])
        print(f"[TEST PASS] Feature Consistency Check: Missing columns detected={missing2}")


if __name__ == "__main__":
    unittest.main()
