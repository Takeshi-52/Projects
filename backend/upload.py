# backend/upload.py
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
from PIL import Image
import shutil
import uuid

APP_DIR = os.path.dirname(__file__)
IMAGES_DIR = os.path.join(APP_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def save_temp(upload: UploadFile, dest: str):
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)

@app.post("/upload-multi")
async def upload_multi(files: List[UploadFile] = File(...)):
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Max 20 images allowed")

    results = []

    for file in files:
        if not file.content_type.startswith("image/"):
            continue
        ext = os.path.splitext(file.filename)[1] or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(IMAGES_DIR, filename)

        save_temp(file, path)

        # resize
        try:
            with Image.open(path) as im:
                im.thumbnail((1280, 1280))
                im.save(path)
        except Exception:
            pass

        results.append({
            "filename": filename,
            "url": f"/images/{filename}"
        })

    return {"count": len(results), "files": results}

@app.get("/images/{filename}")
async def get_img(filename: str):
    path = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404)
    return FileResponse(path)

@app.get("/list")
async def list_images():
    return [f"/images/{f}" for f in os.listdir(IMAGES_DIR)]
