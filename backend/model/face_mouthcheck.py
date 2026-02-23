import cv2
import numpy as np
import torch
from ultralytics import YOLO
import face_alignment
from pathlib import Path

# จัดการ Path ไปหาไฟล์ YOLO
MODEL_DIR = Path(__file__).resolve().parent
YOLO_WEIGHTS = MODEL_DIR / "yolo_face_without_auagment.pt"  

# --- CONFIG สำหรับภาพ 1280x853 โดยเฉพาะ ---
MAR_THRESHOLD = 0.65    # (เกณฑ์อ้าปาก) 0.55-0.60 จะจับคนพูดไมค์/ร้องเพลงได้ดี
MIN_FACE_SIZE = 45      # (ขนาดหน้าขั้นต่ำ) ข้ามใบหน้าที่เล็กกว่า 45x45 พิกเซล (คนอยู่ไกลๆ)
YOLO_CONFIDENCE = 0.45  # (ความมั่นใจ YOLO) ป้องกันการจับวัตถุอื่นเป็นหน้าคน
# ------------------------------------------

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading Mouth Check models on {DEVICE}...")
try:
    yolo_mouth = YOLO(str(YOLO_WEIGHTS))
    
    try:
        lm_type = face_alignment.LandmarksType._2D
    except AttributeError:
        lm_type = face_alignment.LandmarksType.TWO_D
        
    fa_mouth = face_alignment.FaceAlignment(lm_type, device=DEVICE, flip_input=False)
except Exception as e:
    print(f"Error loading models for mouth check: {e}")
    yolo_mouth, fa_mouth = None, None

def calculate_mar(landmarks):
    """คำนวณค่า MAR (Mouth Aspect Ratio) จาก 6 จุดของปาก"""
    A = np.linalg.norm(landmarks[50] - landmarks[58])
    B = np.linalg.norm(landmarks[51] - landmarks[57])
    C = np.linalg.norm(landmarks[52] - landmarks[56])
    D = np.linalg.norm(landmarks[48] - landmarks[54])

    if D == 0: return 0
    return (A + B + C) / (3.0 * D)

def analyze_mouth(image_path: str):
    """
    คืนค่า (passed: bool, score: float, reason: str, drawn_image: numpy_array)
    """
    if yolo_mouth is None or fa_mouth is None:
        return False, 0.0, "Model Error: Mouth models not loaded", None

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Cannot read image at {image_path}")

    h_img, w_img = img.shape[:2]
    img_display = img.copy()
    
    # อัปเดต: เพิ่ม conf เพื่อให้จับเฉพาะหน้าที่ชัดเจนระดับนึง
    results = yolo_mouth.predict(img, conf=YOLO_CONFIDENCE, verbose=False)
    
    # ถ้าไม่เจอหน้าเลย ให้ถือว่าผ่าน (เป็นรูปบรรยากาศ)
    if not results or len(results[0].boxes) == 0:
        return True, 0.0, "ไม่มีบุคคลในภาพ", img_display

    all_passed = True
    reason = "ปากปกติ (Normal)"
    max_mar = 0.0
    faces_checked = 0

    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        
        # อัปเดต: กรองหน้าคนในพื้นหลังที่เล็กเกินไปทิ้ง (สำหรับภาพ 1280x853)
        face_w = x2 - x1
        face_h = y2 - y1
        if face_w < MIN_FACE_SIZE or face_h < MIN_FACE_SIZE:
            continue # หน้าเล็กเกินไป ข้ามไปเลยไม่ต้องเช็คปาก
            
        faces_checked += 1
        
        # เพิ่ม padding 10%
        pad_x = int(face_w * 0.1)
        pad_y = int(face_h * 0.1)
        crop_x1, crop_y1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
        crop_x2, crop_y2 = min(w_img, x2 + pad_x), min(h_img, y2 + pad_y)
        
        face_crop = img[crop_y1:crop_y2, crop_x1:crop_x2]
        if face_crop.size == 0: continue

        face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        
        try:
            preds = fa_mouth.get_landmarks_from_image(face_rgb)
        except:
            preds = None

        color = (0, 255, 0) # สีเขียว (PASS)
        status_text = "PASS"
        mar_val = 0.0

        if preds:
            landmarks = preds[0]
            mar_val = calculate_mar(landmarks)
            max_mar = max(max_mar, mar_val) # เก็บค่า MAR ที่กว้างที่สุดในรูป
            
            # ตัดสินผล
            if mar_val > MAR_THRESHOLD:
                color = (0, 0, 255) # สีแดง (FAIL)
                status_text = "MOUTH OPEN"
                all_passed = False
                reason = f"อ้าปาก/หาว (MAR: {mar_val:.2f})"

            # วาดจุดที่ปาก 12 จุด
            for i in range(48, 60): 
                pt = landmarks[i]
                cv_x = int(pt[0] + crop_x1)
                cv_y = int(pt[1] + crop_y1)
                cv2.circle(img_display, (cv_x, cv_y), 2, (0, 255, 255), -1)

        # วาดกรอบและข้อความบนภาพ
        cv2.rectangle(img_display, (x1, y1), (x2, y2), color, 3)
        
        # ปรับขนาดฟอนต์ให้พอดีกับหน้าจอ
        label = f"{status_text} ({mar_val:.2f})"
        cv2.putText(img_display, label, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # กรณีมีคนในภาพ แต่เล็กเกินไปทั้งหมด ให้ถือว่าผ่าน
    if faces_checked == 0:
        return True, 0.0, "ใบหน้าอยู่ไกลเกินไป", img_display

    return all_passed, max_mar, reason, img_display