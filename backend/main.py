from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from upload import router as upload_router
from brightness_check import router as bright_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routes
app.include_router(upload_router)
app.include_router(bright_router)

# เสิร์ฟโฟลเดอร์ภาพแบบถูกต้อง
app.mount("/images/brightness_pass", StaticFiles(directory="images/brightness_pass"), name="brightness_pass")
app.mount("/images/brightness_fail", StaticFiles(directory="images/brightness_fail"), name="brightness_fail")
app.mount("/images/resized", StaticFiles(directory="images/resized"), name="resized")

