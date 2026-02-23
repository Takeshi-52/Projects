import cv2
import torch
from ultralytics import YOLO
from pathlib import Path

# --- 1. ตั้งค่า Path โมเดล ---
MODEL_DIR = Path(__file__).resolve().parent
PATH_BACKDROP_MODEL = MODEL_DIR / "yolo_backdrop_without_auagment.pt" 
PATH_FACE_MODEL     = MODEL_DIR / "yolo_face_without_auagment.pt"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading Group Photo Pattern models on {DEVICE}...")

try:
    model_backdrop = YOLO(str(PATH_BACKDROP_MODEL))
    model_face     = YOLO(str(PATH_FACE_MODEL))
except Exception as e:
    print(f"Error loading Group models: {e}")
    model_backdrop, model_face = None, None

def check_eye_contact(keypoints, threshold=0.4):
    """ คำนวณ Eye Contact จาก Keypoints """
    if keypoints is None or len(keypoints) < 3:
        return False 
    
    nose = keypoints[2]  
    left_eye = keypoints[0]
    right_eye = keypoints[1]

    dist_left = abs(nose[0] - left_eye[0])
    dist_right = abs(nose[0] - right_eye[0])

    if max(dist_left, dist_right) == 0: return False

    ratio = min(dist_left, dist_right) / max(dist_left, dist_right)
    return ratio > threshold

def analyze_group_pattern(image_path: str):
    """
    คืนค่า (passed: bool, reason: str, drawn_image: numpy_array)
    """
    if model_backdrop is None or model_face is None:
        return False, "Model Error: Models not loaded", None

    img = cv2.imread(str(image_path))
    if img is None:
        return False, f"Error: Cannot read image at {image_path}", None

    draw_img = img.copy()
    
    # --- STEP 1: Detect Backdrop ---
    results_bd = model_backdrop.predict(img, conf=0.8, verbose=False)
    bd_boxes = results_bd[0].boxes if results_bd else []
    
    has_backdrop = len(bd_boxes) > 0
    
    if has_backdrop:
        bd_box = max(bd_boxes, key=lambda b: b.xywh[0][2] * b.xywh[0][3])
        xb1, yb1, xb2, yb2 = map(int, bd_box.xyxy[0])
        cv2.rectangle(draw_img, (xb1, yb1), (xb2, yb2), (0, 255, 255), 3)
        cv2.putText(draw_img, "Backdrop", (xb1, max(yb1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # --- STEP 2: Detect Faces & Eye Contact ---
    results_face = model_face.predict(img, verbose=False)
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
        
        # เช็คการมองกล้อง
        is_looking = False
        if keypoints is not None and len(keypoints) > i:
            is_looking = check_eye_contact(keypoints[i])
        
        if is_looking: 
            looking_camera_count += 1
            color = (0, 255, 0) # เขียว = มองกล้อง
        else:
            color = (0, 0, 255) # แดง = ไม่มองกล้อง
            
        cv2.rectangle(draw_img, (x1, y1), (x2, y2), color, 2)

    # --- STEP 3: วิเคราะห์เงื่อนไข ---
    fail_reasons = []

    # 1. เงื่อนไขจำนวนคน (>= 10)
    if total_people < 10:
        fail_reasons.append(f"คนน้อยไป ({total_people} คน)")
    
    # 2. เงื่อนไขมองกล้อง (> 70%)
    ratio_looking = looking_camera_count / total_people if total_people > 0 else 0
    if ratio_looking < 0.7:
        fail_reasons.append(f"มองกล้องน้อยไป ({int(ratio_looking*100)}%)")

    # 3. เงื่อนไข Backdrop
    if not has_backdrop:
        fail_reasons.append("ไม่มีฉาก Backdrop")

    # --- สรุปผล ---
    passed = len(fail_reasons) == 0
    
    if passed:
        reason = f"รูปถ่ายหมู่ ({total_people} คน)"
        main_color = (0, 255, 0)
    else:
        reason = "ไม่ใช่รูปหมู่ (" + ", ".join(fail_reasons) + ")"
        main_color = (0, 0, 255)

    cv2.putText(draw_img, reason, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, main_color, 2)
    
    info_text = f"People: {total_people} | Gaze: {int(ratio_looking*100)}% | Backdrop: {'YES' if has_backdrop else 'NO'}"
    cv2.putText(draw_img, info_text, (20, draw_img.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    return passed, reason, draw_img