# backend/upload.py

import os
import uuid
import shutil
import cv2
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List
from PIL import Image

# นำเข้าโมเดลต่างๆ สำหรับตรวจสอบคุณภาพ (Quality Check)
from model.photo_exposurecheck import analyze_exposure_simple 
from model.face_eyecheck import analyze_eyes
from model.face_sharpless import analyze_blur
from model.face_mouthcheck import analyze_mouth

# นำเข้าโมเดลสำหรับการจำแนกภาพ (Classification)
from model.pattern1_speaker import analyze_speaker_pattern
from model.pattern2_ambiance import analyze_atmosphere_pattern
from model.pattern3_backdrop import analyze_backdrop_pattern
from model.pattern4_group import analyze_group_pattern

# จัดการโครงสร้างโฟลเดอร์
APP_DIR = os.path.dirname(__file__)
IMAGES_DIR = os.path.join(APP_DIR, "images")
ORIGINAL_DIR = os.path.join(IMAGES_DIR, "original") 
RESIZED_DIR = os.path.join(IMAGES_DIR, "resized")
PHOTO_PASS_DIR = os.path.join(IMAGES_DIR, "photo_pass")
PHOTO_FAIL_DIR = os.path.join(IMAGES_DIR, "photo_fail")

# สร้างโฟลเดอร์ถ้ายังไม่มี
os.makedirs(ORIGINAL_DIR, exist_ok=True) 
os.makedirs(RESIZED_DIR, exist_ok=True)
os.makedirs(PHOTO_PASS_DIR, exist_ok=True)
os.makedirs(PHOTO_FAIL_DIR, exist_ok=True)

router = APIRouter()

def clear_old_files():
    """ฟังก์ชันสำหรับกวาดลบไฟล์รูปภาพเก่าในทุกโฟลเดอร์"""
    folders_to_clear = [ORIGINAL_DIR, RESIZED_DIR, PHOTO_PASS_DIR, PHOTO_FAIL_DIR]
    for folder in folders_to_clear:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

def save_temp(upload: UploadFile, dest: str):
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)

@router.post("/upload-multi")
async def upload_multi(files: List[UploadFile] = File(...)):
    """
    อัปโหลดหลายรูป + ย่อขนาด + ตรวจสอบคุณภาพ
    """
    #clear_old_files()

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Max 20 images allowed")

    results = []

    for file in files:
        if not file.content_type.startswith("image/"):
            continue

        filename = file.filename
        original_path = os.path.join(ORIGINAL_DIR, filename)
        resized_path = os.path.join(RESIZED_DIR, filename)

        # 1. บันทึกรูปต้นฉบับ
        save_temp(file, original_path)

        # 2. ย่อขนาดรูป
        try:
            with Image.open(original_path) as im:
                im = im.convert("RGB") 
                im = im.resize((1280, 853))
                im.save(resized_path)
        except Exception as e:
            print("Resize error:", e)

        # 3. ส่งไปให้โมเดลตรวจสอบคุณภาพ (Quality Check)
        final_passed = True
        final_reason = "ผ่านเกณฑ์"
        final_score = 0.0

        image_to_save = cv2.imread(resized_path)

        try:
            # ด่านแสง
            bright_passed, bright_score, bright_reason = analyze_exposure_simple(resized_path)
            final_score = bright_score 
            
            if not bright_passed:
                final_passed = False
                final_reason = bright_reason

            # ด่านเบลอ
            if final_passed:
                blur_passed, blur_score, blur_reason, drawn_img2 = analyze_blur(resized_path)
                if drawn_img2 is not None:
                    image_to_save = drawn_img2
                if not blur_passed:
                    final_passed = False
                    final_reason = blur_reason
                    final_score = blur_score 

            # ด่านตา
            if final_passed:
                eye_passed, eye_score, eye_reason, drawn_img = analyze_eyes(resized_path)
                if drawn_img is not None:
                    image_to_save = drawn_img
                if not eye_passed:
                    final_passed = False
                    final_reason = eye_reason
                    final_score = eye_score 

            # ด่านปาก
            if final_passed:
                mouth_passed, mouth_score, mouth_reason, drawn_img3 = analyze_mouth(resized_path)
                if drawn_img3 is not None:
                    image_to_save = drawn_img3
                if not mouth_passed:
                    final_passed = False
                    final_reason = mouth_reason
                    final_score = mouth_score 

        except Exception as e:
            print(f"Model Error: {e}")
            final_passed, final_score, final_reason = False, 0.0, "Error processing image"

        # 4. บันทึกผลลัพธ์
        target_dir = PHOTO_PASS_DIR if final_passed else PHOTO_FAIL_DIR
        target_path = os.path.join(target_dir, filename)
        
        if image_to_save is not None:
            cv2.imwrite(target_path, image_to_save)
        else:
            shutil.copy2(resized_path, target_path) 

        folder_url_name = "photo_pass" if final_passed else "photo_fail"
        
        results.append({
            "filename": filename,
            "url": f"/images/{folder_url_name}/{filename}",
            "status": "Passed" if final_passed else "Rejected",
            "defect_reason": final_reason,
            "score": round(final_score, 2)
        })

    return {"count": len(results), "files": results}


# --- Endpoint สำหรับดึงรูปภาพ ---
@router.get("/images/original/{filename}")
async def get_img_original(filename: str):
    path = os.path.join(ORIGINAL_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404)
    return FileResponse(path)

@router.get("/images/photo_pass/{filename}")
async def get_img_pass(filename: str):
    path = os.path.join(PHOTO_PASS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404)
    return FileResponse(path)

@router.get("/images/photo_fail/{filename}")
async def get_img_fail(filename: str):
    path = os.path.join(PHOTO_FAIL_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404)
    return FileResponse(path)

@router.post("/clear-images")
async def api_clear_images():
    """API สำหรับเคลียร์รูปเก่าในโฟลเดอร์ทิ้ง (เรียกใช้ 1 ครั้งก่อนเริ่มอัปโหลดชุดใหม่)"""
    clear_old_files()
    return {"message": "เคลียร์ไฟล์เก่าเรียบร้อย"}

# --- Endpoint สำหรับจำแนกภาพ (Classification) ---
@router.post("/classify-passed")
async def classify_passed_images():
    if not os.path.exists(PHOTO_PASS_DIR):
        return {"message": "ไม่มีโฟลเดอร์รูปที่ผ่านเกณฑ์", "data": []}

    classified_results = []
    
    # ตัวนับสถิติ
    stats = {
        "speaker": 0,
        "group": 0,
        "backdrop": 0,
        "atmos": 0
    }

    for filename in os.listdir(PHOTO_PASS_DIR):
        file_path = os.path.join(PHOTO_PASS_DIR, filename)

        clean_file_path = os.path.join(RESIZED_DIR, filename)
        
        if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            
            # --- ด่านที่ 1: วิทยากร ---
            is_speaker, reason, img = analyze_speaker_pattern(clean_file_path)
            if is_speaker:
                category, final_reason = "วิทยากร", reason
                stats["speaker"] += 1
            else:
                # --- ด่านที่ 2: รูปถ่ายหมู่ (>= 10 คน) ---
                is_group, reason, img = analyze_group_pattern(clean_file_path)
                if is_group:
                    category, final_reason = "รูปหมู่", reason
                    stats["group"] += 1
                else:
                    # --- ด่านที่ 3: Backdrop (1-5 คน) ---
                    is_bd, reason, img = analyze_backdrop_pattern(clean_file_path)
                    if is_bd:
                        category, final_reason = "Backdrop", reason
                        stats["backdrop"] += 1
                    else:
                        # --- ด่านที่ 4: บรรยากาศ (แคนดิด) ---
                        is_atmos, reason, img = analyze_atmosphere_pattern(clean_file_path)
                        if is_atmos:
                            category, final_reason = "บรรยากาศ", reason
                            stats["atmos"] += 1
                        else:
                            # ถ้าตกทุกด่าน (เช่น คน 6-9 คน หน้า Backdrop)
                            category = "อื่นๆ (รอจำแนก)"
                            final_reason = reason # ดึงเหตุผลสุดท้ายมาโชว์

            classified_results.append({
                "filename": filename,
                "category": category,
                "reason": final_reason
            })

    return {
        "message": "จำแนกภาพเสร็จสิ้น",
        "total": len(classified_results),
        "speaker_count": stats["speaker"],
        "group_count": stats["group"],
        "backdrop_count": stats["backdrop"],
        "atmos_count": stats["atmos"],
        "data": classified_results
    }