import cv2
import numpy as np
import torch
from ultralytics import YOLO
from pathlib import Path

# --- 1. ตั้งค่า Path โมเดล ---
MODEL_DIR = Path(__file__).resolve().parent
PATH_BACKDROP_MODEL = MODEL_DIR / "yolo_backdrop_without_auagment.pt" 
PATH_SPEAKER_MODEL  = MODEL_DIR / "yolo_speaker_without_auagment.pt"  
PATH_FACE_MODEL     = MODEL_DIR / "yolo_face_without_auagment.pt" 

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading Atmosphere Pattern models on {DEVICE}...")

models = {}
try:
    models['backdrop'] = YOLO(str(PATH_BACKDROP_MODEL))
    models['speaker']  = YOLO(str(PATH_SPEAKER_MODEL))
    models['face']     = YOLO(str(PATH_FACE_MODEL))
except Exception as e:
    print(f"Error loading Atmosphere models: {e}")

def check_eye_contact(keypoints):
    """ คำนวณ Eye Contact จาก Keypoints """
    if keypoints is None or len(keypoints) < 3: return False
    
    nose = keypoints[2]
    left_eye = keypoints[0]
    right_eye = keypoints[1]
    
    dist_left = abs(nose[0] - left_eye[0])
    dist_right = abs(nose[0] - right_eye[0])
    
    if max(dist_left, dist_right) == 0: return False
    ratio = min(dist_left, dist_right) / max(dist_left, dist_right)
    return ratio > 0.5

# --- จุดสำคัญ: ชื่อฟังก์ชันตรงกับที่ upload.py เรียกใช้ ---
def analyze_atmosphere_pattern(image_path: str):
    """
    คืนค่า (passed: bool, reason: str, drawn_image: numpy_array)
    """
    if 'backdrop' not in models or 'speaker' not in models or 'face' not in models:
        return False, "Model Error: Models not loaded", None

    img = cv2.imread(str(image_path))
    if img is None: 
        return False, f"Error: Cannot read image at {image_path}", None
        
    draw_img = img.copy()
    fail_reasons = []
    
    # =========================================================================
    # STEP 1: Anti-Speaker Check (ถ้าเจอไมค์/โพเดียม = ตก)
    # =========================================================================
    results_speaker = models['speaker'].predict(img, conf=0.8, verbose=False)
    if results_speaker and len(results_speaker[0].boxes) > 0:
        names_speaker = results_speaker[0].names
        for box in results_speaker[0].boxes:
            cls_id = int(box.cls[0])
            label = names_speaker[cls_id].lower()
            
            if label in ['microphone', 'podium', 'mic']:
                fail_reasons.append(f"มีวิทยากร ({label})")
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(draw_img, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(draw_img, "Speaker Tool", (x1, max(y1-10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # =========================================================================
    # STEP 2: Anti-Backdrop Check (ถ้าเจอฉาก Backdrop = ตก)
    # =========================================================================
    results_bd = models['backdrop'].predict(img, conf=0.8, verbose=False)
    if results_bd and len(results_bd[0].boxes) > 0:
        names_bd = results_bd[0].names
        for box in results_bd[0].boxes:
            cls_id = int(box.cls[0])
            label = names_bd[cls_id].lower()
            
            if 'backdrop' in label:
                fail_reasons.append("มีป้าย Backdrop (เป็นรูปถ่ายหมู่)")
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(draw_img, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(draw_img, "Backdrop", (x1, max(y1-10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # =========================================================================
    # STEP 3: Atmosphere Logic Check (เช็คคน + การมองกล้อง)
    # =========================================================================
    results_face = models['face'].predict(img, verbose=False)
    face_boxes = results_face[0].boxes if results_face else []
    
    keypoints = None
    if results_face and hasattr(results_face[0], 'keypoints') and results_face[0].keypoints is not None:
        try:
            keypoints = results_face[0].keypoints.xy.cpu().numpy()
        except:
            pass
            
    total_people = len(face_boxes)
    looking_camera_count = 0

    for i, box in enumerate(face_boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        is_looking = False
        if keypoints is not None and len(keypoints) > i:
            is_looking = check_eye_contact(keypoints[i])
            
        if is_looking:
            looking_camera_count += 1
            color = (0, 0, 255) # มองกล้อง (วาดสีแดง)
        else:
            color = (0, 255, 0) # แคนดิด (วาดสีเขียว)
            
        cv2.rectangle(draw_img, (x1, y1), (x2, y2), color, 2)

    # --- Logic 3.1: ต้องมีคนอย่างน้อย 1 คน ---
    if total_people < 1:
        fail_reasons.append("ไม่พบบุคคล")

    # --- Logic 3.2: Candid Ratio (ต้องมองกล้องไม่เกิน 50%) ---
    ratio_looking = looking_camera_count / total_people if total_people > 0 else 0
    if ratio_looking > 0.5: 
        fail_reasons.append(f"ตั้งใจมองกล้อง ({int(ratio_looking*100)}%)")

    # =========================================================================
    # สรุปผล (Final Decision)
    # =========================================================================
    passed = len(fail_reasons) == 0
    
    if passed:
        reason = "ภาพบรรยากาศ/แคนดิด"
        status_color = (0, 255, 0)
    else:
        # รวมเหตุผลทั้งหมดเข้าด้วยกัน
        reason = "ไม่ใช่บรรยากาศ (" + ", ".join(fail_reasons) + ")"
        status_color = (0, 0, 255)

    cv2.putText(draw_img, reason, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
    return passed, reason, draw_img