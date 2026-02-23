import cv2
import torch
from ultralytics import YOLO
from pathlib import Path

# --- 1. ตั้งค่า Path โมเดลให้อ้างอิงจากโฟลเดอร์ปัจจุบัน ---
MODEL_DIR = Path(__file__).resolve().parent
PATH_CUSTOM_MODEL = MODEL_DIR / "yolo_speaker_without_auagment.pt"   
PATH_FACE_MODEL   = MODEL_DIR / "yolo_face_without_auagment.pt"

# --- 2. ตั้งค่า ID ของ Class ---
CLASS_ID = {
    'mic': 0,
    'screen': 1,
    'podium': 2,
    'backdrop': 3
}

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading Speaker Pattern models on {DEVICE}...")

try:
    model_custom = YOLO(str(PATH_CUSTOM_MODEL))
    model_face   = YOLO(str(PATH_FACE_MODEL))
except Exception as e:
    print(f"Error loading models: {e}")
    model_custom, model_face = None, None

def is_overlapping(box1, box2):
    """ฟังก์ชันช่วยคำนวณว่ากล่อง 2 อัน ทับกันไหม"""
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])
    
    # ถ้าด้านขวามากกว่าด้านซ้าย และ ด้านล่างมากกว่าด้านบน = มีพื้นที่ทับกัน
    return x_right > x_left and y_bottom > y_top

# --- จุดสำคัญ: ต้องชื่อฟังก์ชันนี้ เพื่อให้ upload.py เรียกใช้ได้ ---
def analyze_speaker_pattern(image_path: str):
    """
    คืนค่า (passed: bool, reason: str, drawn_image: numpy_array)
    """
    if model_custom is None or model_face is None:
        return False, "Model Error: Speaker models not loaded", None

    # อ่านรูปภาพ
    img = cv2.imread(str(image_path))
    if img is None:
        return False, f"Error: Cannot read image at {image_path}", None

    draw_img = img.copy()
    
    # ตัวแปรเก็บสถานะต่างๆ
    faces_boxes = []     # เก็บกล่องหน้าคน
    tools_boxes = []     # เก็บกล่องไมค์/โพเดียม
    has_context = False  # มีจอหรือป้ายงานไหม
    
    # ==========================================
    # STEP 1: ตรวจจับวัตถุ (Mic, Podium, Screen, Backdrop)
    # ==========================================
    results_custom = model_custom.predict(img, verbose=False)
    
    if results_custom and len(results_custom[0].boxes) > 0:
        for box in results_custom[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            if conf > 0.4: # กรองความมั่นใจ 40%
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # 1.1 เช็ค Context
                if cls_id in [CLASS_ID['screen'], CLASS_ID['backdrop']]:
                    has_context = True
                    cv2.rectangle(draw_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(draw_img, "Context", (x1, max(y1-5, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # 1.2 เก็บพิกัดเครื่องมือ (Mic, Podium)
                elif cls_id in [CLASS_ID['mic'], CLASS_ID['podium']]:
                    tools_boxes.append([x1, y1, x2, y2])
                    cv2.rectangle(draw_img, (x1, y1), (x2, y2), (0, 165, 255), 2)
                    name = "Mic" if cls_id == CLASS_ID['mic'] else "Podium"
                    cv2.putText(draw_img, name, (x1, max(y1-5, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

    # ==========================================
    # STEP 2: นับหน้าคน (Face Detection)
    # ==========================================
    results_face = model_face.predict(img, verbose=False)
    
    if results_face and len(results_face[0].boxes) > 0:
        for box in results_face[0].boxes:
            if float(box.conf[0]) > 0.5:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                faces_boxes.append([x1, y1, x2, y2])
                cv2.rectangle(draw_img, (x1, y1), (x2, y2), (255, 255, 0), 2)

    face_count = len(faces_boxes)

    # ==========================================
    # STEP 3: ตรวจสอบ Action (คน vs เครื่องมือ)
    # ==========================================
    has_action = False
    for face_box in faces_boxes:
        for tool_box in tools_boxes:
            if is_overlapping(face_box, tool_box):
                has_action = True
                break 
        if has_action: break

    # ==========================================
    # STEP 4: สรุปผลตามเงื่อนไข (Logic Gate)
    # ==========================================
    passed = False
    reason = ""
    color_status = (0, 0, 255) # สีแดง

    # เช็คเงื่อนไขตามลำดับ
    if face_count == 0:
        reason = "ไม่พบบุคคล (No Person)"
    elif face_count > 2:
        reason = f"คนเยอะเกินไป ({face_count} คน)"
    elif not has_context:
        reason = "ไม่มีจอ/ป้ายงาน (No Context)"
    elif not has_action:
        reason = "ไม่ได้ใช้ไมค์/โพเดียม (No Action)"
    else:
        passed = True
        reason = "วิทยากร (Speaker Pattern)"
        color_status = (0, 255, 0) # สีเขียว

    # เขียนผลลัพธ์บนภาพมุมซ้ายบน
    cv2.putText(draw_img, reason, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_status, 2)
    
    return passed, reason, draw_img