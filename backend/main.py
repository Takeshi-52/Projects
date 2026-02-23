import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from upload import router as upload_router
from model.photo_exposurecheck import router as exposure_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routes
app.include_router(upload_router)
app.include_router(exposure_router)

# สร้างโฟลเดอร์ไว้ล่วงหน้าเพื่อป้องกัน Error ตอนเซิร์ฟเวอร์เริ่มทำงาน
os.makedirs("images/photo_pass", exist_ok=True)
os.makedirs("images/photo_fail", exist_ok=True)
os.makedirs("images/resized", exist_ok=True)
os.makedirs("images/original", exist_ok=True)

# เสิร์ฟโฟลเดอร์ภาพแบบถูกต้อง (เปลี่ยนชื่อให้ตรงกับ upload.py แล้ว)
app.mount("/images/photo_pass", StaticFiles(directory="images/photo_pass"), name="photo_pass")
app.mount("/images/photo_fail", StaticFiles(directory="images/photo_fail"), name="photo_fail")
app.mount("/images/resized", StaticFiles(directory="images/resized"), name="resized")
app.mount("/images/original", StaticFiles(directory="images/original"), name="original")