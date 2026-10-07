"""
Visual Inspection Module for Predictive Maintenance.
Integrates YOLO11 object detection, Gold Reference image comparison,
image quality & ROI alignment, visual health scoring, temporal validation,
and sensor-visual multi-modal fusion.
"""

from .config import VisualConfig
from .detector import YOLO11Detector
from .reference_validator import validate_gold_reference
from .reference_comparator import ReferenceComparator
from .visual_health import VisualHealthEngine
from .temporal_validator import TemporalValidator
from .fusion_engine import MultiModalFusionEngine

__all__ = [
    "VisualConfig",
    "YOLO11Detector",
    "validate_gold_reference",
    "ReferenceComparator",
    "VisualHealthEngine",
    "TemporalValidator",
    "MultiModalFusionEngine",
]
