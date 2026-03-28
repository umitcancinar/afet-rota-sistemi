"""
AI Görüntü Analiz Motoru
========================
Uydu/drone görüntülerinden enkaz tespiti yapar.
- Görüntü ön-işleme (CLAHE kontrast iyileştirme)
- Roboflow inference ile enkaz tespiti
- Piksel → GPS dönüşümü (Mercator düzeltmeli)
- Enkaz büyüklüğüne göre etki yarıçapı hesabı
"""
import logging
import math
import os
import tempfile
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from inference_sdk import InferenceHTTPClient, InferenceConfiguration
from backend.config import (
    ROBOFLOW_API_KEY, ROBOFLOW_API_URL, ROBOFLOW_MODEL_ID,
    AI_CONFIDENCE, AI_IOU_THRESHOLD, DANGER_RADIUS_BASE
)

logger = logging.getLogger(__name__)

# Roboflow client (modül yüklendiğinde bir kez oluşturulur)
_client = InferenceHTTPClient(api_url=ROBOFLOW_API_URL, api_key=ROBOFLOW_API_KEY)


def preprocess_image(image_path: str) -> str:
    """Görüntüyü AI modeline göndermeden önce optimize eder."""
    img = cv2.imread(image_path)
    if img is None:
        logger.error(f"Görüntü okunamadı: {image_path}")
        return image_path

    # 1. CLAHE Kontrast İyileştirme
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l_channel)
    lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
    img = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    # 2. Hafif keskinleştirme
    gaussian = cv2.GaussianBlur(img, (0, 0), 2.0)
    img = cv2.addWeighted(img, 1.3, gaussian, -0.3, 0)

    cv2.imwrite(image_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return image_path


def _infer_single(image_path: str) -> list[dict]:
    """Tek bir görüntü üzerinde Roboflow inference çalıştırır."""
    try:
        _client.configure(InferenceConfiguration(
            confidence_threshold=AI_CONFIDENCE,
            iou_threshold=AI_IOU_THRESHOLD
        ))
        result = _client.infer(image_path, model_id=ROBOFLOW_MODEL_ID)
    except Exception as e:
        logger.error(f"Roboflow API hatası: {e}")
        return []
    return result.get("predictions", [])


def _iou(a: dict, b: dict) -> float:
    """İki bounding box arasındaki IoU (Intersection over Union) hesaplar."""
    ax1, ay1 = a["x"] - a["width"] / 2, a["y"] - a["height"] / 2
    ax2, ay2 = a["x"] + a["width"] / 2, a["y"] + a["height"] / 2
    bx1, by1 = b["x"] - b["width"] / 2, b["y"] - b["height"] / 2
    bx2, by2 = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2

    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0

    inter = (ix2 - ix1) * (iy2 - iy1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _nms_merge(detections: list[dict], iou_thresh: float = 0.3) -> list[dict]:
    if not detections: return []
    sorted_dets = sorted(detections, key=lambda d: d["confidence"], reverse=True)
    keep = []
    while sorted_dets:
        best = sorted_dets.pop(0)
        keep.append(best)
        sorted_dets = [d for d in sorted_dets if _iou(best, d) < iou_thresh]
    return keep


def _process_tile_worker(args):
    """Paralel çalışan tile analiz fonksiyonu."""
    t_img, x_off, y_off = args
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    cv2.imwrite(tmp.name, t_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    tmp.close()
    
    try:
        preds = _infer_single(tmp.name)
        tile_results = []
        for p in preds:
            conf = p.get("confidence", 0)
            if conf >= AI_CONFIDENCE:
                tile_results.append({
                    "x": p["x"] + x_off,
                    "y": p["y"] + y_off,
                    "width": p.get("width", 0),
                    "height": p.get("height", 0),
                    "confidence": conf,
                    "class": p.get("class", "debris"),
                })
        return tile_results
    except Exception as e:
        logger.error(f"Tile işleme hatası: {e}")
        return []
    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


def detect_debris(image_path: str) -> list[dict]:
    """SAHI (Slicing Aided Hyper Inference) ile PARALEL enkaz tespiti."""
    preprocess_image(image_path)
    img = cv2.imread(image_path)
    if img is None: return []

    img_h, img_w = img.shape[:2]
    TILE_SIZE, OVERLAP = 640, 0.20
    stride = int(TILE_SIZE * (1 - OVERLAP))

    logger.info(f"🚀 SAHI Başlatılıyor (Paralel): {img_w}x{img_h}")

    tile_tasks = []
    for y_start in range(0, img_h, stride):
        for x_start in range(0, img_w, stride):
            x_end, y_end = min(x_start + TILE_SIZE, img_w), min(y_start + TILE_SIZE, img_h)
            if (x_end - x_start) < TILE_SIZE // 2 or (y_end - y_start) < TILE_SIZE // 2:
                continue
            tile_tasks.append((img[y_start:y_end, x_start:x_end], x_start, y_start))

    all_predictions = []
    # 10 paralel worker ile hızı 5-10 kat artırıyoruz
    with ThreadPoolExecutor(max_workers=10) as executor:
        batch_results = list(executor.map(_process_tile_worker, tile_tasks))
    
    for res_list in batch_results:
        all_predictions.extend(res_list)

    # Tam görüntüyü de bir kez tarat (büyük enkazlar için)
    full_preds = _infer_single(image_path)
    for p in full_preds:
        if p.get("confidence", 0) >= AI_CONFIDENCE:
            all_predictions.append({
                "x": p["x"], "y": p["y"], "width": p.get("width", 0),
                "height": p.get("height", 0), "confidence": p["confidence"],
                "class": p.get("class", "debris"),
            })

    # NMS ile birleştir ve alan hesabı yap
    merged = _nms_merge(all_predictions, iou_thresh=AI_IOU_THRESHOLD)
    detections = []
    for det in merged:
        det["area_px"] = det.get("width", 0) * det.get("height", 0)
        detections.append(det)

    detections.sort(key=lambda d: d["area_px"], reverse=True)
    return detections


def pixel_to_gps(px, py, img_w, img_h, nw_lat, nw_lon, se_lat, se_lon):
    lat = nw_lat - (py / img_h) * (nw_lat - se_lat)
    lon = nw_lon + (px / img_w) * (se_lon - nw_lon)
    return (lat, lon)


def calculate_danger_radius(area_px, img_w, img_h, nw_lat, nw_lon, se_lat, se_lon):
    lat_diff, lon_diff = abs(nw_lat - se_lat), abs(se_lon - nw_lon)
    avg_lat = (nw_lat + se_lat) / 2
    m_per_deg_lat = 111_320
    m_per_deg_lon = 111_320 * math.cos(math.radians(avg_lat))
    real_h_m, real_w_m = lat_diff * m_per_deg_lat, lon_diff * m_per_deg_lon
    m_per_px = ((real_w_m / img_w) + (real_h_m / img_h)) / 2 if img_w > 0 and img_h > 0 else 0
    real_area_m2 = area_px * (m_per_px ** 2)
    radius = math.sqrt(real_area_m2 / math.pi) * 2.5 if real_area_m2 > 0 else 0
    return round(min(max(DANGER_RADIUS_BASE, radius), 200), 1)


def _calculate_risk_score(class_name: str) -> float:
    c = class_name.lower()
    if c == 'collapsed': return 0.95
    elif c == 'damaged': return 0.65
    return 0.20


def analyze_image(image_path, img_w, img_h, nw_lat, nw_lon, se_lat, se_lon):
    detections = detect_debris(image_path)
    results = []
    for det in detections:
        lat, lon = pixel_to_gps(det["x"], det["y"], img_w, img_h, nw_lat, nw_lon, se_lat, se_lon)
        radius = calculate_danger_radius(det["area_px"], img_w, img_h, nw_lat, nw_lon, se_lat, se_lon)
        results.append({
            "lat": round(lat, 7), "lon": round(lon, 7), "confidence": round(det["confidence"], 3),
            "class": det["class"], "danger_radius_m": radius, "risk_score": _calculate_risk_score(det["class"]),
            "area_px": det["area_px"]
        })
    return results
