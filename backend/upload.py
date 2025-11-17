# backend/upload.py

import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List
from PIL import Image
import shutil
import uuid

APP_DIR = os.path.dirname(__file__)

# โฟลเดอร์หลัก
IMAGES_DIR = os.path.join(APP_DIR, "images")
RESIZED_DIR = os.path.join(IMAGES_DIR, "resized")

# สร้างโฟลเดอร์ถ้ายังไม่มี
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(RESIZED_DIR, exist_ok=True)

router = APIRouter()

def save_temp(upload: UploadFile, dest: str):
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)


@router.post("/upload-multi")
async def upload_multi(files: List[UploadFile] = File(...)):
    """
    อัปโหลดหลายรูป + resize เก็บไว้ใน images/resized/
    """
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Max 20 images allowed")

    results = []

    for file in files:
        if not file.content_type.startswith("image/"):
            continue

        ext = os.path.splitext(file.filename)[1] or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"

        # path original
        original_path = os.path.join(IMAGES_DIR, filename)

        # path resized
        resized_path = os.path.join(RESIZED_DIR, filename)

        # save original temp
        save_temp(file, original_path)

        # resize + save
        try:
            with Image.open(original_path) as im:
                im = im.convert("RGB")  # ป้องกัน PNG บางกรณี error
                im = im.resize((1280, 853))
                im.save(resized_path)
        except Exception as e:
            print("Resize error:", e)

        results.append({
            "filename": filename,
            "url": f"/images/{filename}",
            "resized": f"/images/resized/{filename}"
        })

    return {"count": len(results), "files": results}


@router.get("/images/{filename}")
async def get_img(filename: str):
    path = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404)
    return FileResponse(path)


@router.get("/images/resized/{filename}")
async def get_resized(filename: str):
    path = os.path.join(RESIZED_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404)
    return FileResponse(path)


@router.get("/list")
async def list_images():
    """
    ส่งลิสต์รูป original เท่านั้น
    """
    files = [f"/images/{f}" for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]
    return files
