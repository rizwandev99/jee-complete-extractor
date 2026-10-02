import os
import json
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sys

# Add scripts directory to path to import extraction pipeline
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
CROPS_DIR = os.path.join(OUTPUT_DIR, "question_crops")
DIAGRAMS_DIR = os.path.join(OUTPUT_DIR, "diagrams")
QUESTIONS_FILE = os.path.join(OUTPUT_DIR, "questions.json")

# Ensure required directories exist
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CROPS_DIR, exist_ok=True)
os.makedirs(DIAGRAMS_DIR, exist_ok=True)

if SCRIPTS_DIR not in sys.path:
    sys.path.append(SCRIPTS_DIR)

from extract_pipeline import run_extraction

app = FastAPI(title="JEE Complete Extractor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Mounts
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")
app.mount("/dashboard", StaticFiles(directory=DASHBOARD_DIR), name="dashboard")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_file = os.path.join(DASHBOARD_DIR, "dashboard.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)

@app.get("/api/questions")
async def get_questions():
    if os.path.exists(QUESTIONS_FILE):
        try:
            with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return JSONResponse(content=data)
        except Exception as e:
            return JSONResponse(content=[], status_code=200)
    return JSONResponse(content=[], status_code=200)

@app.post("/api/clear-all")
async def clear_all():
    # 1. Clear all question crops
    if os.path.exists(CROPS_DIR):
        for fname in os.listdir(CROPS_DIR):
            fpath = os.path.join(CROPS_DIR, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
            except Exception as e:
                print(f"Error removing {fpath}: {e}")

    # 2. Clear all isolated diagrams
    if os.path.exists(DIAGRAMS_DIR):
        for fname in os.listdir(DIAGRAMS_DIR):
            fpath = os.path.join(DIAGRAMS_DIR, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
            except Exception as e:
                print(f"Error removing {fpath}: {e}")

    # 3. Clear uploaded PDF files to make it completely fresh
    if os.path.exists(UPLOADS_DIR):
        for fname in os.listdir(UPLOADS_DIR):
            fpath = os.path.join(UPLOADS_DIR, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
            except Exception as e:
                print(f"Error removing {fpath}: {e}")

    # 4. Clean any temp files in output dir
    for fname in os.listdir(OUTPUT_DIR):
        if fname.startswith("temp_") or fname.endswith(".tmp"):
            fpath = os.path.join(OUTPUT_DIR, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
            except Exception:
                pass

    # 5. Reset questions.json to empty list []
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

    return JSONResponse(content={"status": "cleared", "count": 0, "message": "Everything completely wiped and reset to brand new initial state!"})

@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    target_path = os.path.join(UPLOADS_DIR, file.filename)
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run extraction pipeline on uploaded PDF
    questions = run_extraction(target_path)
    return JSONResponse(content={
        "status": "success",
        "count": len(questions),
        "questions": questions
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
