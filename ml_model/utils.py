import os
import io
import base64
import shutil
from typing import Union, List, Dict, Any, Tuple, Optional
from PIL import Image
import numpy as np
import cv2


def load_image(image_input: Union[str, bytes, Image.Image, np.ndarray]) -> np.ndarray:
    """
    Standardize image input into an RGB numpy array uint8 [H, W, 3].
    Supports file path, raw bytes, PIL Image, or numpy array.
    """
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image not found at path: {image_input}")
        img_pil = Image.open(image_input).convert("RGB")
        return np.array(img_pil)
    elif isinstance(image_input, bytes):
        img_pil = Image.open(io.BytesIO(image_input)).convert("RGB")
        return np.array(img_pil)
    elif isinstance(image_input, Image.Image):
        return np.array(image_input.convert("RGB"))
    elif isinstance(image_input, np.ndarray):
        if len(image_input.shape) == 2:
            return cv2.cvtColor(image_input, cv2.COLOR_GRAY2RGB)
        elif image_input.shape[2] == 4:
            return cv2.cvtColor(image_input, cv2.COLOR_RGBA2RGB)
        return image_input
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")


def preprocess_image_for_model(
    image_rgb: np.ndarray,
    target_size: Tuple[int, int] = (640, 640)
) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    Letterbox / resize image preserving aspect ratio with zero padding.
    Returns:
        padded_image, scale_factor, (pad_w, pad_h)
    """
    h, w, _ = image_rgb.shape
    tw, th = target_size
    scale = min(tw / w, th / h)
    nw, nh = int(w * scale), int(h * scale)

    resized = cv2.resize(image_rgb, (nw, nh), interpolation=cv2.INTER_LINEAR)
    pad_w = (tw - nw) // 2
    pad_h = (th - nh) // 2

    canvas = np.zeros((th, tw, 3), dtype=np.uint8)
    canvas[pad_h:pad_h + nh, pad_w:pad_w + nw] = resized

    return canvas, scale, (pad_w, pad_h)


def extract_contours_and_polygons(
    binary_mask: np.ndarray,
    min_area: int = 50,
    approx_epsilon: float = 0.015
) -> List[Dict[str, Any]]:
    """
    Extract bounding boxes and polygon boundaries from a binary thresholded mask.
    Returns list of objects with [x1, y1, x2, y2] bounding boxes and [ [x, y], ... ] polygon points.
    """
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions: List[Dict[str, Any]] = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        # Bounding box
        x, y, w, h = cv2.boundingRect(cnt)
        box = [int(x), int(y), int(x + w), int(y + h)]

        # Centroid
        m = cv2.moments(cnt)
        if m["m00"] > 0:
            cx = int(m["m10"] / m["m00"])
            cy = int(m["m01"] / m["m00"])
        else:
            cx, cy = int(x + w / 2), int(y + h / 2)

        # Approximate contour to polygon
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, approx_epsilon * peri, True)
        polygon = [[int(pt[0][0]), int(pt[0][1])] for pt in approx]

        regions.append({
            "box": box,
            "polygon": polygon,
            "area": float(area),
            "centroid": [cx, cy]
        })

    # Sort largest infected area first
    regions.sort(key=lambda r: r["area"], reverse=True)
    return regions


def overlay_heatmap_on_image(
    image_rgb: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.45,
    colormap: int = cv2.COLORMAP_JET
) -> np.ndarray:
    """
    Blend normalized 2D heatmap [0, 1] with RGB image using selected colormap.
    Returns composite RGB image.
    """
    # Normalize heatmap to [0, 255]
    heatmap_norm = np.clip(heatmap, 0.0, 1.0)
    heatmap_uint8 = np.uint8(255 * heatmap_norm)

    heatmap_color_bgr = cv2.applyColorMap(heatmap_uint8, colormap)
    heatmap_color_rgb = cv2.cvtColor(heatmap_color_bgr, cv2.COLOR_BGR2RGB)

    overlay = cv2.addWeighted(image_rgb, 1.0 - alpha, heatmap_color_rgb, alpha, 0)
    return overlay


def image_to_base64(image_rgb: np.ndarray, format: str = "PNG") -> str:
    """Convert RGB numpy array to base64 data URI string (PNG or JPEG)."""
    pil_img = Image.fromarray(image_rgb)
    buf = io.BytesIO()
    pil_img.save(buf, format=format)
    mime = "image/png" if format.upper() == "PNG" else "image/jpeg"
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def save_image_to_destinations(
    image_rgb: np.ndarray,
    primary_path: str,
    secondary_paths: Optional[List[str]] = None,
    format: str = "PNG"
) -> str:
    """
    Save image to primary path and copy/save to secondary paths.
    """
    os.makedirs(os.path.dirname(primary_path), exist_ok=True)
    img_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(primary_path, img_bgr)

    if secondary_paths:
        for p in secondary_paths:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            try:
                shutil.copyfile(primary_path, p)
            except Exception:
                cv2.imwrite(p, img_bgr)

    return primary_path
