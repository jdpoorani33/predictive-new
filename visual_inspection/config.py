import os

class VisualConfig:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

    # Model & Weights Paths
    MODEL_DIR = os.path.join(BASE_DIR, "models")
    DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, "best.pt")
    YOLO_BASE_CHECKPOINT = "yolo11n.pt"  # Pretrained YOLO11 nano baseline

    # Reference Image Directory
    GOLD_REF_DIR = os.path.join(BASE_DIR, "reference", "gold_reference")

    # Dataset Directories
    DATASET_DIR = os.path.join(BASE_DIR, "dataset")
    SAMPLE_IMAGES_DIR = os.path.join(BASE_DIR, "sample_images")

    # Defect Classes
    CLASSES = [
        "crack",
        "corrosion",
        "leakage",
        "belt_damage",
        "component_damage",
        "overheating",
        "smoke"
    ]

    # Class Severity Weights (1.0 = minor, 3.0 = severe)
    CLASS_SEVERITY_WEIGHTS = {
        "crack": 2.2,
        "corrosion": 1.8,
        "leakage": 2.5,
        "belt_damage": 2.8,
        "component_damage": 3.0,
        "overheating": 2.6,
        "smoke": 3.0
    }

    # YOLO Detection Thresholds
    CONF_THRESHOLD = 0.35
    HIGH_CONF_THRESHOLD = 0.70
    IOU_THRESHOLD = 0.45

    # Image Quality Thresholds
    MIN_RESOLUTION = (200, 200)
    BLUR_LAPLACIAN_VAR_MIN = 35.0  # Below this is considered blurry
    EXPOSURE_MIN_MEAN = 20.0       # Below this is too dark (underexposed)
    EXPOSURE_MAX_MEAN = 235.0      # Above this is washed out (overexposed)

    # Reference Comparison Thresholds & Weights
    SSIM_WEIGHT = 0.40
    FEATURE_MATCH_WEIGHT = 0.30
    EDGE_DIFF_WEIGHT = 0.30

    SIMILARITY_EXCELLENT = 85.0
    SIMILARITY_HEALTHY = 70.0
    SIMILARITY_WARNING = 50.0

    # Visual Health Scoring Thresholds (0-100)
    HEALTH_EXCELLENT_MIN = 90.0
    HEALTH_HEALTHY_MIN = 75.0
    HEALTH_WARNING_MIN = 50.0

    # Temporal Validation Window Size
    TEMPORAL_WINDOW_SIZE = 5

    # Sensor Disagreement Thresholds
    TEMP_SENSOR_HIGH_THRESHOLD = 85.0  # deg C
    VIB_SENSOR_HIGH_THRESHOLD = 1.2   # mm/s
