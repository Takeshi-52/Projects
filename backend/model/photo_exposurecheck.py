import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from pathlib import Path
import shutil

router = APIRouter()

# จัดการ Path ให้ถูกต้อง
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"
RESIZED_DIR = IMAGES_DIR / "resized"

# อัปเดตโฟลเดอร์ให้เป็น photo_pass และ photo_fail
PHOTO_PASS = IMAGES_DIR / "photo_pass"
PHOTO_FAIL = IMAGES_DIR / "photo_fail"

# สร้างโฟลเดอร์ปลายทางถ้ายังไม่มี
PHOTO_PASS.mkdir(parents=True, exist_ok=True)
PHOTO_FAIL.mkdir(parents=True, exist_ok=True)

def analyze_exposure_simple(image_path: str):
    """
    รับ Path ของไฟล์ภาพ (ที่อยู่ใน resized) แล้วประมวลผลแสง
    """
    # 1. อ่านภาพ
    img_bgr = cv2.imread(str(image_path))

    if img_bgr is None:
        raise ValueError(f"Cannot decode image at {image_path}")

    # 2. แปลงเป็น Grayscale เพื่อดูความสว่างรวม (0-255)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # 3. คำนวณค่าสถิติพื้นฐาน
    mean_val = float(np.mean(gray)) # ค่าความสว่างเฉลี่ย
    total_pixels = gray.size
    
    # นับจำนวนพิกเซลที่ "มืดจัด" (Shadow Clipping) และ "สว่างจัด" (Highlight Clipping)
    dark_pixels = np.count_nonzero(gray < 20)
    bright_pixels = np.count_nonzero(gray > 235)
    
    dark_pct = float((dark_pixels / total_pixels) * 100)
    bright_pct = float((bright_pixels / total_pixels) * 100)

    # เพิ่มใหม่: หาเปอร์เซ็นไทล์ที่ 95 (พิกเซลที่สว่างที่สุด 95% ของภาพ อยู่ที่ระดับไหน)
    p95_val = float(np.percentile(gray, 95))

    # 4. ตัดสินผล (Verdict Logic)
    passed = True
    reason = "Normal Exposure"
    
    # เงื่อนไข: ถ้าขาวโพลนเกิน 5% -> OVER, ถ้าดำจมเกิน 15% -> UNDER
    # หมายเหตุ: ถ้าภาพงานอีเวนต์มีสีขาวเยอะแล้วภาพตกหมด อาจจะปรับ 5.0 เป็น 10.0 หรือ 15.0 ตามความเหมาะสมนะครับ
    if bright_pct > 50.0:  
        passed = False
        reason = f"OVEREXPOSED (Highlight {bright_pct:.1f}%)"
    elif dark_pct > 30.0:
        passed = False
        reason = f"UNDEREXPOSED (Shadow {dark_pct:.1f}%)"
        
    # --- เงื่อนไขที่เพิ่มใหม่: ดักจับภาพที่มืด/แบน ขาดไฮไลท์ ---
    elif p95_val < 150: 
        passed = False
        reason = f"UNDEREXPOSED / FLAT (Lacks Highlights, P95={p95_val:.1f})"
        
    # ปรับเงื่อนไขค่าเฉลี่ยให้จับภาพมืดได้ดีขึ้นนิดหน่อย
    elif mean_val > 200:
        passed = False
        reason = "WARNING: Very Bright"
    elif mean_val < 70: # ขยับจาก 75 เป็น 70 ตามโค้ดใหม่
        passed = False
        reason = "WARNING: Very Dark"

    return passed, mean_val, reason


@router.get("/check-brightness/{filename}")
async def check_resized_image(filename: str):
    """
    API สำหรับตรวจสอบรูปภาพ 1 รูปที่อยู่ในโฟลเดอร์ resized
    """
    file_path = RESIZED_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Image {filename} not found in resized folder")

    try:
        passed, mean_light, reason = analyze_exposure_simple(file_path)
        
        # คัดลอกภาพไปยังโฟลเดอร์ pass/fail ตามผลลัพธ์
        save_to = PHOTO_PASS if passed else PHOTO_FAIL
        save_path = save_to / filename
        shutil.copy2(file_path, save_path)
        
    except Exception as e:
        print(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail="Error processing image")

    return {
        "filename": filename,
        "brightness": round(mean_light, 2),
        "passed": passed,
        "reason": reason,
        "saved_to": f"/images/photo_{'pass' if passed else 'fail'}/{filename}"
    }


@router.post("/check-all-resized")
async def check_all_resized_images():
    """
    API สำหรับสั่งรันตรวจรูปภาพ *ทั้งหมด* ที่อยู่ในโฟลเดอร์ resized ในครั้งเดียว
    """
    results = []
    
    for file_path in RESIZED_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            try:
                passed, mean_light, reason = analyze_exposure_simple(file_path)
                
                # คัดลอกไปโฟลเดอร์ pass/fail
                save_to = PHOTO_PASS if passed else PHOTO_FAIL
                shutil.copy2(file_path, save_to / file_path.name)
                
                results.append({
                    "filename": file_path.name,
                    "passed": passed,
                    "reason": reason,
                    "brightness": round(mean_light, 2)
                })
            except Exception as e:
                print(f"Skipping {file_path.name} due to error: {e}")

    return {
        "total_processed": len(results),
        "results": results
    }


# routes สำหรับ list รูปภาพ
@router.get("/photo-pass")
async def list_pass():
    return [f"/images/photo_pass/{f.name}" for f in PHOTO_PASS.iterdir() if f.is_file()]

@router.get("/photo-fail")
async def list_fail():
    return [f"/images/photo_fail/{f.name}" for f in PHOTO_FAIL.iterdir() if f.is_file()]