import os
import cv2
import numpy as np
from .config import VisualConfig

def generate_industrial_component_image(
    component_type: str = "motor_belt",
    has_defect: bool = False,
    defect_type: str = "crack",
    lighting_offset: float = 0.0,
    noise_level: float = 0.0
) -> np.ndarray:
    """
    Generates realistic synthetic industrial component images for baseline testing.
    component_type options: "motor_belt", "bearing_unit", "turbine_casing", "heat_exchanger", "gearbox"
    """
    w, h = 640, 640
    img = np.full((h, w, 3), 45, dtype=np.uint8)  # Metallic dark gray background

    # Component base structures
    if component_type == "motor_belt":
        # Draw motor pulleys
        cv2.circle(img, (180, 320), 100, (80, 80, 85), -1)
        cv2.circle(img, (180, 320), 100, (140, 140, 145), 6)
        cv2.circle(img, (180, 320), 30, (30, 30, 35), -1)

        cv2.circle(img, (460, 320), 80, (80, 80, 85), -1)
        cv2.circle(img, (460, 320), 80, (140, 140, 145), 6)
        cv2.circle(img, (460, 320), 25, (30, 30, 35), -1)

        # Draw drive belt
        cv2.line(img, (180, 220), (460, 240), (25, 25, 28), 24)
        cv2.line(img, (180, 420), (460, 400), (25, 25, 28), 24)

        # Subtle belt texture
        for x in range(200, 440, 15):
            cv2.line(img, (x, 220), (x, 240), (45, 45, 50), 2)

    elif component_type == "bearing_unit":
        # Draw outer bearing housing & inner race
        cv2.circle(img, (320, 320), 220, (100, 100, 105), -1)
        cv2.circle(img, (320, 320), 220, (170, 170, 175), 8)
        cv2.circle(img, (320, 320), 150, (40, 40, 45), -1)
        cv2.circle(img, (320, 320), 80, (120, 120, 125), -1)

        # Ball bearings
        for angle in range(0, 360, 45):
            rad = np.radians(angle)
            cx = int(320 + 115 * np.cos(rad))
            cy = int(320 + 115 * np.sin(rad))
            cv2.circle(img, (cx, cy), 22, (200, 200, 205), -1)

    elif component_type == "turbine_casing":
        # Draw cylindrical turbine casing and bolts
        cv2.rectangle(img, (120, 120), (520, 520), (90, 95, 100), -1)
        cv2.rectangle(img, (120, 120), (520, 520), (160, 165, 170), 8)
        cv2.circle(img, (320, 320), 130, (50, 55, 60), -1)

        # Flange bolt holes
        for x in [150, 490]:
            for y in range(150, 500, 70):
                cv2.circle(img, (x, y), 12, (30, 30, 35), -1)

    else:
        # Default metallic gearbox block
        cv2.rectangle(img, (150, 150), (490, 490), (110, 110, 115), -1)
        cv2.rectangle(img, (150, 150), (490, 490), (180, 180, 185), 6)
        cv2.circle(img, (320, 320), 100, (60, 60, 65), -1)

    # Apply lighting variation
    if lighting_offset != 0.0:
        img = np.clip(img.astype(np.float32) + lighting_offset, 0, 255).astype(np.uint8)

    # Add Defects if requested
    if has_defect:
        if defect_type == "crack":
            # Draw prominent jagged structural crack with branching
            pts1 = np.array([[200, 210], [240, 270], [280, 260], [350, 340], [400, 390]], np.int32)
            pts2 = np.array([[280, 260], [320, 240], [360, 220]], np.int32)
            cv2.polylines(img, [pts1], False, (10, 10, 10), 8)
            cv2.polylines(img, [pts1], False, (0, 0, 220), 3)
            cv2.polylines(img, [pts2], False, (10, 10, 10), 6)
            cv2.polylines(img, [pts2], False, (0, 0, 200), 2)

        elif defect_type == "corrosion":
            # Rust / corrosion patch
            cv2.ellipse(img, (320, 240), (100, 60), 25, 0, 360, (20, 80, 180), -1)  # BGR Brownish rust
            cv2.ellipse(img, (340, 250), (80, 40), 15, 0, 360, (30, 100, 210), -1)

        elif defect_type == "belt_damage":
            # Frayed belt cut and tear mark
            cv2.rectangle(img, (260, 200), (360, 260), (15, 15, 15), -1)
            cv2.line(img, (240, 210), (380, 250), (0, 0, 240), 6)
            cv2.line(img, (250, 390), (370, 430), (0, 0, 240), 6)

        elif defect_type == "overheating":
            # Thermal discoloration burn mark
            cv2.circle(img, (320, 320), 110, (30, 70, 160), -1)  # Dark reddish heat burn
            cv2.circle(img, (320, 320), 75, (20, 40, 110), -1)

        elif defect_type == "leakage":
            # Fluid leak streak
            pts = np.array([[320, 180], [330, 280], [350, 420], [335, 500]], np.int32)
            cv2.polylines(img, [pts], False, (15, 50, 30), 18)  # Dark oil streak

    # Add noise if requested
    if noise_level > 0.0:
        noise = np.random.normal(0, noise_level, img.shape).astype(np.float32)
        img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    return img

def populate_sample_references_and_images():
    """Generates and saves Gold References for PLC_01 to PLC_05 and sample test images."""
    plcs_config = {
        "PLC_01": ("motor_belt", "component_01.jpg"),
        "PLC_02": ("turbine_casing", "component_01.jpg"),
        "PLC_03": ("bearing_unit", "component_01.jpg"),
        "PLC_04": ("gearbox", "component_01.jpg"),
        "PLC_05": ("motor_belt", "component_01.jpg"),
    }

    print("Generating Gold References and test images...")

    for plc_id, (comp_type, fname) in plcs_config.items():
        plc_ref_dir = os.path.join(VisualConfig.GOLD_REF_DIR, plc_id)
        os.makedirs(plc_ref_dir, exist_ok=True)

        # Gold Reference (100% Healthy)
        gold_img = generate_industrial_component_image(comp_type, has_defect=False)
        gold_path = os.path.join(plc_ref_dir, fname)
        cv2.imwrite(gold_path, gold_img)

        # Sample Current Healthy Image (slight lighting variation)
        curr_healthy = generate_industrial_component_image(comp_type, has_defect=False, lighting_offset=5.0)
        sample_h_dir = os.path.join(VisualConfig.SAMPLE_IMAGES_DIR, plc_id)
        os.makedirs(sample_h_dir, exist_ok=True)
        cv2.imwrite(os.path.join(sample_h_dir, "healthy.jpg"), curr_healthy)

        # Sample Defective Image
        defect_type = "crack" if plc_id in ["PLC_01", "PLC_03"] else ("corrosion" if plc_id == "PLC_02" else "belt_damage")
        curr_defective = generate_industrial_component_image(comp_type, has_defect=True, defect_type=defect_type)
        cv2.imwrite(os.path.join(sample_h_dir, "defective.jpg"), curr_defective)

    print("Gold References and sample dataset images populated successfully.")

if __name__ == "__main__":
    populate_sample_references_and_images()
