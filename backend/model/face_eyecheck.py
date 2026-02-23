import cv2
import numpy as np
import torch
from ultralytics import YOLO
import face_alignment
from pathlib import Path

# จัดการ Path ไปหาไฟล์ YOLO
MODEL_DIR = Path(__file__).resolve().parent
YOLO_MODEL_PATH = MODEL_DIR / "yolo_face_without_auagment.pt" 
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading YOLO and Face Alignment on {DEVICE}...")
try:
    yolo = YOLO(str(YOLO_MODEL_PATH))
    fa = face_alignment.FaceAlignment(face_alignment.LandmarksType.TWO_D, 
                                      device=DEVICE, flip_input=False)
except Exception as e:
    print(f"Error loading models: {e}")
    yolo, fa = None, None

def calculate_ear(eye_points):
    A = np.linalg.norm(eye_points[1] - eye_points[5])
    B = np.linalg.norm(eye_points[2] - eye_points[4])
    C = np.linalg.norm(eye_points[0] - eye_points[3])
    return (A + B) / (2.0 * C) if C != 0 else 0

def analyze_eyes(image_path: str):
    """
    คืนค่า (passed: bool, lowest_ear: float, reason: str, drawn_image: numpy_array)
    """
    if yolo is None or fa is None:
        return False, 0.0, "Model Error: Models not loaded", None

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Cannot read image at {image_path}")
    
    img_display = img.copy()
    
    # 1. ให้ YOLO หาใบหน้า (ใช้ conf=0.5)
    results = yolo.predict(img, conf=0.5, verbose=False)
    
    all_passed = True
    reason = "ลืมตาปกติ (Eyes Open)"
    lowest_ear = 1.0 # เก็บค่า EAR ที่ต่ำที่สุดในรูป
    face_found = False

    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy() 
        for box in boxes:
            face_found = True
            x1, y1, x2, y2 = map(int, box[:4])
            
            face_crop = img[y1:y2, x1:x2]
            if face_crop.size == 0: continue

            face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
            
            # 2. หา Landmarks
            try:
                preds = fa.get_landmarks_from_image(face_rgb)
            except:
                preds = None

            status = "UNKNOWN"
            color = (0, 0, 0)
            ear_avg = 0.0

            if preds:
                landmarks = preds[0]
                right_eye_pts = landmarks[36:42]
                left_eye_pts = landmarks[42:48]
                
                r_ear = calculate_ear(right_eye_pts)
                l_ear = calculate_ear(left_eye_pts)
                ear_avg = (r_ear + l_ear) / 2.0
                lowest_ear = min(lowest_ear, ear_avg)
                
                # --- LOGIC ตัดสิน ---
                if ear_avg < 0.18: # (ตัวเลขเกณฑ์หลับตาของคุณ)
                    status = "FAIL (Closed)"
                    color = (0, 0, 255) 
                    all_passed = False
                    reason = f"หลับตา/มองต่ำ (EAR < {ear_avg:.2f})"
                else:
                    status = "PASS"
                    color = (0, 255, 0)
            else:
                status = "No Landmarks"
                color = (0, 255, 255)

            # วาดผลลัพธ์ลงภาพ (เอาไว้โชว์บนหน้าเว็บ)
            cv2.rectangle(img_display, (x1, y1), (x2, y2), color, 2)
            label = f"{status} ({ear_avg:.2f})"
            cv2.putText(img_display, label, (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # กรณีไม่มีคนในรูปเลย
    if not face_found:
        lowest_ear = 0.0

    return all_passed, lowest_ear, reason, img_display