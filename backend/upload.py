# backend/upload.py

import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List
from PIL import Image
import shutil
import uuid

# 1. นำเข้าฟังก์ชันจากไฟล์ brightness_check.py ของคุณ
# (แก้ชื่อฟังก์ชันให้ตรงกับที่คุณเขียนไว้ในไฟล์นั้นนะครับ)
from brightness_check import check_image_brightness 

APP_DIR = os.path.dirname(__file__)

# จัดการโครงสร้างโฟลเดอร์ใหม่
IMAGES_DIR = os.path.join(APP_DIR, "images")
ORIGINAL_DIR = os.path.join(IMAGES_DIR, "original") # เพิ่มโฟลเดอร์เก็บไฟล์ต้นฉบับ
RESIZED_DIR = os.path.join(IMAGES_DIR, "resized")

# สร้างโฟลเดอร์ถ้ายังไม่มี
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(ORIGINAL_DIR, exist_ok=True) # ตรวจสอบ/สร้างโฟลเดอร์ original
os.makedirs(RESIZED_DIR, exist_ok=True)

router = APIRouter()

def save_temp(upload: UploadFile, dest: str):
    # บันทึกไฟล์ลงในตำแหน่งที่ระบุ
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)

@router.post("/upload-multi")
async def upload_multi(files: List[UploadFile] = File(...)):
    """
    อัปโหลดหลายรูป + resize
    - ต้นฉบับเก็บใน images/original/
    - ย่อขนาดเก็บใน images/resized/
    """
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Max 20 images allowed")

    results = []

    for file in files:
        if not file.content_type.startswith("image/"):
            continue

        ext = os.path.splitext(file.filename)[1] or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"

        # เปลี่ยน path การเก็บต้นฉบับไปที่ ORIGINAL_DIR
        original_path = os.path.join(ORIGINAL_DIR, filename)

        # path สำหรับไฟล์ที่ย่อขนาดแล้ว (RESIZED_DIR)
        resized_path = os.path.join(RESIZED_DIR, filename)

        # บันทึกไฟล์ต้นฉบับลงโฟลเดอร์ original
        save_temp(file, original_path)

        # ย่อขนาดรูปและบันทึกลงโฟลเดอร์ resized
        try:
            with Image.open(original_path) as im:
                im = im.convert("RGB")  # ป้องกัน PNG บางกรณี error
                im = im.resize((1280, 853))
                im.save(resized_path)
        except Exception as e:
            print("Resize error:", e)

        results.append({
            "filename": filename,
            "url": f"/images/original/{filename}", # อัปเดต URL ให้ตรงกับโฟลเดอร์ใหม่
            "resized": f"/images/resized/{filename}"
        })

    return {"count": len(results), "files": results}


@router.get("/images/original/{filename}")
async def get_img(filename: str):
    # ดึงรูปต้นฉบับจากโฟลเดอร์ original
    path = os.path.join(ORIGINAL_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404)
    return FileResponse(path)


@router.get("/images/resized/{filename}")
async def get_resized(filename: str):
    # ดึงรูปที่ย่อขนาดแล้วจากโฟลเดอร์ resized
    path = os.path.join(RESIZED_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404)
    return FileResponse(path)


@router.get("/list")
async def list_images():
    """
    ส่งลิสต์รูป original เท่านั้น
    """
    # เปลี่ยนพาร์ทไปดึงไฟล์จากโฟลเดอร์ ORIGINAL_DIR
    files = [f"/images/original/{f}" for f in os.listdir(ORIGINAL_DIR) if os.path.isfile(os.path.join(ORIGINAL_DIR, f))]
    return files