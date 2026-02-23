# backend/model/blur_check.py

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from pathlib import Path

# จัดการ Path ไปหาไฟล์โมเดล YOLO
MODEL_DIR = Path(__file__).resolve().parent
YOLO_WEIGHTS = MODEL_DIR / "yolo_face_without_auagment.pt"  # ต้องแน่ใจว่ามีไฟล์นี้ในโฟลเดอร์ model นะครับ

SHARPNESS_THRESHOLD = 1.2      
MIN_FACE_RATIO = 0.05             
MAX_REALISTIC_SHARPNESS = 50.0     

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading Blur Check YOLO on {DEVICE}...")
try:
    yolo_blur = YOLO(str(YOLO_WEIGHTS))
except Exception as e:
    print(f"Error loading YOLO for blur: {e}")
    yolo_blur = None

def calculate_tenengrad(gray):
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    g2 = gx**2 + gy**2
    return float(np.mean(g2) / 1000.0)

def analyze_blur(image_path: str):
    """
    คืนค่า (passed: bool, score: float, reason: str, drawn_image: numpy_array)
    """
    if yolo_blur is None:
        return False, 0.0, "Model Error: Blur YOLO not loaded", None

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Cannot read image at {image_path}")

    h_img, w_img = img.shape[:2]
    img_display = img.copy()
    
    results = yolo_blur.predict(img, verbose=False)
    
    # กรณี 1: ไม่มีคนในรูปเลย 
    # (ผมตั้งให้เป็น PASS ชั่วคราว เพื่อให้รูปภาพบรรยากาศเวที/สถานที่ ผ่านได้ครับ ถ้าอยากให้ตกแก้เป็น False ได้เลย)
    if not results or len(results[0].boxes) == 0:
        return True, 0.0, "ไม่มีบุคคลในภาพ (Scene/Background)", img_display

    usable_faces = 0
    max_sharpness = 0.0
    reasons = []

    for i, box in enumerate(results[0].boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        face_h = y2 - y1
        face_ratio = face_h / h_img
        
        if face_ratio < MIN_FACE_RATIO:
            continue 

        pad_x = int((x2 - x1) * 0.1)
        pad_y = int((y2 - y1) * 0.1)
        crop_x1, crop_y1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
        crop_x2, crop_y2 = min(w_img, x2 + pad_x), min(h_img, y2 + pad_y)
        
        face_crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
        if face_crop.size == 0: continue

        gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        sharpness_val = calculate_tenengrad(gray_face)
        
        max_sharpness = max(max_sharpness, sharpness_val)
        
        is_clear_enough = sharpness_val >= SHARPNESS_THRESHOLD
        is_not_artificial = sharpness_val <= MAX_REALISTIC_SHARPNESS
        
        is_pass = is_clear_enough and is_not_artificial
        
        if is_pass:
            status_text = "PASS"
            color = (0, 255, 0)
            usable_faces += 1
        elif not is_clear_enough:
            status_text = "BLUR"
            color = (0, 0, 255)
            reasons.append("ภาพเบลอ (Blurry)")
        else:
            status_text = "ARTIFACT" 
            color = (0, 255, 255)
            reasons.append("ไม่ใช่บุคคลจริง (Artifact/Screen)")

        # วาดผลลัพธ์
        cv2.rectangle(img_display, (x1, y1), (x2, y2), color, 3)
        label_plot = f"{status_text} S:{sharpness_val:.1f}"
        (text_w, text_h), _ = cv2.getTextSize(label_plot, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(img_display, (x1, y1 - text_h - 10), (x1 + text_w, y1), color, -1)
        cv2.putText(img_display, label_plot, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # กรณี 2: มีคนในรูป แต่เล็กเกินไปทั้งหมด (< 5%) ถือว่าผ่าน (เป็นรูประยะไกล)
    if len(results[0].boxes) > 0 and usable_faces == 0 and len(reasons) == 0:
         return True, max_sharpness, "ใบหน้าเล็กเกินไป (Too small to check)", img_display

    # กรณี 3: ตัดสินตามเงื่อนไขของคุณ
    final_passed = usable_faces > 0
    final_reason = "ชัดเจน (Sharp)" if final_passed else reasons[0]
    
    return final_passed, max_sharpness, final_reason, img_display