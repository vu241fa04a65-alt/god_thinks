"""
Utility to generate 10 labeled leaf images for demo and Grad-CAM overlay PNGs.
"""
import os
import csv
import math
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATASET_DIR = os.path.join(BASE_DIR, "ml_model", "datasets", "sample")
OVERLAYS_DIR = os.path.join(BASE_DIR, "backend", "storage", "sample_overlays")
BACKEND_OVERLAYS_DIR = os.path.join(BASE_DIR, "backend", "storage", "overlays")
BACKEND_UPLOADS_DIR = os.path.join(BASE_DIR, "backend", "storage", "uploads")

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(OVERLAYS_DIR, exist_ok=True)
os.makedirs(BACKEND_OVERLAYS_DIR, exist_ok=True)
os.makedirs(BACKEND_UPLOADS_DIR, exist_ok=True)

SAMPLE_CLASSES = [
    {
        "filename": "01_tomato_early_blight.jpg",
        "crop": "Tomato",
        "disease": "Tomato Early Blight",
        "severity": "Moderate",
        "confidence": 0.948,
        "leaf_color": (34, 139, 34),
        "spots": [(180, 160, 35, (139, 69, 19)), (220, 240, 28, (160, 82, 45)), (140, 260, 22, (101, 67, 33))],
        "overlay_filename": "overlay_tomato_early_blight.png"
    },
    {
        "filename": "02_tomato_late_blight.jpg",
        "crop": "Tomato",
        "disease": "Tomato Late Blight",
        "severity": "High",
        "confidence": 0.965,
        "leaf_color": (46, 125, 50),
        "spots": [(200, 180, 50, (60, 40, 20)), (160, 270, 40, (70, 50, 25)), (250, 140, 30, (80, 60, 30))],
        "overlay_filename": "overlay_tomato_late_blight.png"
    },
    {
        "filename": "03_tomato_healthy.jpg",
        "crop": "Tomato",
        "disease": "Tomato Healthy",
        "severity": "None",
        "confidence": 0.991,
        "leaf_color": (56, 142, 60),
        "spots": [],
        "overlay_filename": "overlay_tomato_healthy.png"
    },
    {
        "filename": "04_potato_early_blight.jpg",
        "crop": "Potato",
        "disease": "Potato Early Blight",
        "severity": "Moderate",
        "confidence": 0.932,
        "leaf_color": (46, 117, 89),
        "spots": [(190, 170, 32, (120, 70, 20)), (230, 230, 25, (140, 80, 30))],
        "overlay_filename": "overlay_potato_early_blight.png"
    },
    {
        "filename": "05_potato_late_blight.jpg",
        "crop": "Potato",
        "disease": "Potato Late Blight",
        "severity": "Severe",
        "confidence": 0.978,
        "leaf_color": (40, 110, 80),
        "spots": [(170, 150, 55, (50, 30, 15)), (230, 220, 48, (65, 40, 20))],
        "overlay_filename": "overlay_potato_late_blight.png"
    },
    {
        "filename": "06_corn_common_rust.jpg",
        "crop": "Corn",
        "disease": "Corn Common Rust",
        "severity": "Moderate",
        "confidence": 0.954,
        "leaf_color": (67, 160, 71),
        "spots": [(180, 120, 15, (205, 92, 92)), (200, 180, 18, (178, 34, 34)), (220, 250, 16, (165, 42, 42)), (170, 290, 14, (139, 0, 0))],
        "overlay_filename": "overlay_corn_common_rust.png"
    },
    {
        "filename": "07_corn_northern_leaf_blight.jpg",
        "crop": "Corn",
        "disease": "Corn Northern Leaf Blight",
        "severity": "High",
        "confidence": 0.925,
        "leaf_color": (76, 175, 80),
        "spots": [(200, 200, 60, (130, 110, 70)), (190, 280, 45, (110, 90, 50))],
        "overlay_filename": "overlay_corn_northern_blight.png"
    },
    {
        "filename": "08_apple_scab.jpg",
        "crop": "Apple",
        "disease": "Apple Scab",
        "severity": "Moderate",
        "confidence": 0.941,
        "leaf_color": (50, 130, 50),
        "spots": [(160, 160, 26, (40, 35, 20)), (240, 200, 30, (50, 45, 25)), (190, 260, 22, (45, 40, 22))],
        "overlay_filename": "overlay_apple_scab.png"
    },
    {
        "filename": "09_rice_blast.jpg",
        "crop": "Rice",
        "disease": "Rice Blast",
        "severity": "High",
        "confidence": 0.963,
        "leaf_color": (80, 160, 60),
        "spots": [(200, 150, 24, (139, 69, 19)), (195, 220, 30, (105, 105, 105)), (205, 290, 20, (160, 82, 45))],
        "overlay_filename": "overlay_rice_blast.png"
    },
    {
        "filename": "10_wheat_yellow_rust.jpg",
        "crop": "Wheat",
        "disease": "Wheat Yellow Rust",
        "severity": "High",
        "confidence": 0.957,
        "leaf_color": (90, 170, 70),
        "spots": [(190, 140, 14, (218, 165, 32)), (205, 200, 16, (205, 133, 63)), (195, 260, 15, (218, 165, 32)), (200, 310, 12, (184, 134, 11))],
        "overlay_filename": "overlay_wheat_yellow_rust.png"
    }
]


def create_leaf_image(meta: dict) -> Image.Image:
    """Create realistic synthetic leaf image with veins and lesion spots."""
    img = Image.new("RGB", (400, 400), color=(245, 245, 240))
    draw = ImageDraw.Draw(img)

    # 1. Background soft vignette
    for r in range(250, 200, -10):
        draw.ellipse([200 - r, 200 - r, 200 + r, 200 + r], fill=(235 + (250 - r) // 5, 238, 233))

    # 2. Leaf Body (Pointed Oval / Cordate polygon)
    leaf_poly = [
        (200, 30),
        (280, 120),
        (310, 230),
        (270, 330),
        (200, 370),
        (130, 330),
        (90, 230),
        (120, 120)
    ]
    draw.polygon(leaf_poly, fill=meta["leaf_color"])

    # 3. Leaf Veins (Main Stem & Secondary Ribs)
    vein_color = (max(0, meta["leaf_color"][0] - 20), min(255, meta["leaf_color"][1] + 30), max(0, meta["leaf_color"][2] - 20))
    draw.line([(200, 40), (200, 365)], fill=vein_color, width=4)

    # Secondary lateral veins
    for y, dy in [(120, 40), (170, 50), (220, 50), (270, 45), (320, 35)]:
        draw.line([(200, y), (200 + dy + 30, y - 25)], fill=vein_color, width=2)
        draw.line([(200, y), (200 - dy - 30, y - 25)], fill=vein_color, width=2)

    # 4. Disease Lesion Spots
    for cx, cy, rad, col in meta["spots"]:
        # Concentric necrotic rings
        for r_step in range(rad, 0, -4):
            ring_col = (
                min(255, col[0] + r_step * 2),
                max(0, col[1] - r_step),
                max(0, col[2] - r_step)
            )
            draw.ellipse([cx - r_step, cy - r_step, cx + r_step, cy + r_step], fill=ring_col)

        # Yellowish chlorotic halo around lesion
        halo_box = [cx - rad - 5, cy - rad - 5, cx + rad + 5, cy + rad + 5]
        draw.ellipse(halo_box, outline=(200, 190, 80), width=2)

    # Soft blur to simulate natural biological texture
    img = img.filter(ImageFilter.SMOOTH_MORE)
    return img


def create_gradcam_overlay(meta: dict) -> Image.Image:
    """Generate Grad-CAM heatmap overlay (RGBA) highlighting disease lesion regions."""
    overlay = Image.new("RGBA", (400, 400), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    spots = meta["spots"]
    if not spots:
        # Healthy leaf: diffuse mild green/blue attention
        draw.ellipse([160, 140, 240, 260], fill=(0, 180, 255, 60))
        draw.ellipse([180, 170, 220, 230], fill=(0, 230, 120, 90))
    else:
        # Disease hotspots: yellow/red high attention centers surrounded by cyan/green gradients
        for cx, cy, rad, _ in spots:
            for r_dist, col_alpha in [
                (rad + 45, (0, 0, 255, 45)),       # Deep blue low attention
                (rad + 30, (0, 220, 255, 75)),     # Cyan gradient
                (rad + 18, (80, 255, 50, 110)),    # Green medium attention
                (rad + 8, (255, 230, 0, 150)),     # Yellow high attention
                (rad - 4, (255, 50, 0, 180)),      # Red peak attention
            ]:
                if r_dist > 0:
                    draw.ellipse([cx - r_dist, cy - r_dist, cx + r_dist, cy + r_dist], fill=col_alpha)

    # Gaussian blur to create smooth Grad-CAM gradient contours
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=8))
    return overlay


def generate_all_assets():
    csv_rows = [["image_name", "crop", "disease", "severity", "confidence_target", "overlay_name"]]

    for meta in SAMPLE_CLASSES:
        # 1. Create and save leaf image
        leaf_img = create_leaf_image(meta)
        dataset_path = os.path.join(DATASET_DIR, meta["filename"])
        uploads_path = os.path.join(BACKEND_UPLOADS_DIR, meta["filename"])
        leaf_img.save(dataset_path, "JPEG", quality=95)
        leaf_img.save(uploads_path, "JPEG", quality=95)

        # 2. Create and save Grad-CAM overlay
        overlay_img = create_gradcam_overlay(meta)
        overlay_path = os.path.join(OVERLAYS_DIR, meta["overlay_filename"])
        backend_overlay_path = os.path.join(BACKEND_OVERLAYS_DIR, meta["overlay_filename"])
        overlay_img.save(overlay_path, "PNG")
        overlay_img.save(backend_overlay_path, "PNG")

        csv_rows.append([
            meta["filename"],
            meta["crop"],
            meta["disease"],
            meta["severity"],
            meta["confidence"],
            meta["overlay_filename"]
        ])
        print(f"Generated: {meta['filename']} -> {meta['overlay_filename']}")

    # 3. Write labels.csv
    csv_path = os.path.join(DATASET_DIR, "labels.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)

    print(f"SUCCESS: Generated {len(SAMPLE_CLASSES)} leaf images, overlays, and labels.csv at {DATASET_DIR}")


if __name__ == "__main__":
    generate_all_assets()
