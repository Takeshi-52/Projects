import cv2
import torch
from ultralytics import YOLO
from pathlib import Path

# --- 1. ตั้งค่า Path โมเดล ---
MODEL_DIR = Path(__file__).resolve().parent
PATH_BACKDROP_MODEL = MODEL_DIR / "yolo_backdrop_without_auagment.pt" 
PATH_FACE_MODEL     = MODEL_DIR / "yolo_face_without_auagment.pt"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading Backdrop Pattern models on {DEVICE}...")

try:
    model_backdrop = YOLO(str(PATH_BACKDROP_MODEL))
    model_face     = YOLO(str(PATH_FACE_MODEL))
except Exception as e:
    print(f"Error loading Backdrop models: {e}")
    model_backdrop, model_face = None, None

def analyze_backdrop_pattern(image_path: str):
    """
    คืนค่า (passed: bool, reason: str, drawn_image: numpy_array)
    """
    if model_backdrop is None or model_face is None:
        return False, "Model Error: Models not loaded", None

    img = cv2.imread(str(image_path))
    if img is None:
        return False, f"Error: Cannot read image at {image_path}", None

    draw_img = img.copy()

    # --- STEP 1: หา Backdrop (เพิ่มความเข้มงวดเป็น 0.75 เพื่อกันพลาด) ---
    has_backdrop = False
    bd_results = model_backdrop.predict(img, conf=0.75, verbose=False)
    
    if bd_results and len(bd_results[0].boxes) > 0:
        for box in bd_results[0].boxes:
            if int(box.cls[0]) == 0:
                has_backdrop = True
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(draw_img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                cv2.putText(draw_img, f"Backdrop ({float(box.conf[0]):.2f})", (x1, max(y1-15, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                break 

    # --- STEP 2: นับหน้าคน (ลดความเข้มงวดลงเหลือ 0.35 เพื่อให้นับคนใส่แมสก์ได้) ---
    face_count = 0
    face_results = model_face.predict(img, conf=0.35, verbose=False)
    
    if face_results and len(face_results[0].boxes) > 0:
        for box in face_results[0].boxes:
            face_count += 1
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(draw_img, (x1, y1), (x2, y2), (255, 255, 0), 2)

    # --- STEP 3: สรุปผล ---
    passed = False
    reason = ""
    color = (0, 0, 255) # สีแดง

    if not has_backdrop:
        reason = "ไม่มีฉาก Backdrop"
    elif face_count == 0:
        reason = "ไม่พบบุคคล"
    elif face_count > 5:
        reason = f"คนเยอะเกินไป ({face_count} คน)"
    else:
        passed = True
        reason = f"ถ่ายรูปหน้า Backdrop ({face_count} คน)"
        color = (0, 255, 0) # สีเขียว

    # เขียนผลลัพธ์บนภาพ
    cv2.putText(draw_img, reason, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
    
    return passed, reason, draw_img