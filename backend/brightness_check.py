from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from PIL import Image
from io import BytesIO
import numpy as np

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
BRIGHT_PASS = BASE_DIR / "images" / "brightness_pass"
BRIGHT_FAIL = BASE_DIR / "images" / "brightness_fail"

BRIGHT_PASS.mkdir(parents=True, exist_ok=True)
BRIGHT_FAIL.mkdir(parents=True, exist_ok=True)

def check_brightness(image: Image.Image):
    gray = image.convert("L")
    arr = np.array(gray)
    mean_val = float(arr.mean())  # ensure float, not numpy type

    MIN_LIGHT = 60
    MAX_LIGHT = 200

    passed = bool(MIN_LIGHT <= mean_val <= MAX_LIGHT)
    return mean_val, passed


@router.post("/check-brightness")
async def brightness_check(file: UploadFile = File(...)):
    try:
        image = Image.open(BytesIO(await file.read()))
    except:
        raise HTTPException(status_code=400, detail="Invalid image")

    mean_light, passed = check_brightness(image)

    save_to = BRIGHT_PASS if passed else BRIGHT_FAIL
    save_path = save_to / file.filename
    image.save(save_path)

    return {
        "filename": file.filename,
        "brightness": mean_light,
        "passed": passed,
        "saved_to": f"/brightness/{'pass' if passed else 'fail'}/{file.filename}"
    }


# new route: list pass images
@router.get("/brightness-pass")
async def list_pass():
    return [f"/brightness/pass/{f.name}" for f in BRIGHT_PASS.iterdir() if f.is_file()]


# new route: list fail images
@router.get("/brightness-fail")
async def list_fail():
    return [f"/brightness/fail/{f.name}" for f in BRIGHT_FAIL.iterdir() if f.is_file()]
