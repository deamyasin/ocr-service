from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
from pathlib import Path
import shutil
import uuid
from datetime import datetime

import config
from task_queue.task_queue import process_file, process_directory, get_task_progress

app = FastAPI(
    title="Advanced OCR Service",
    description="High-quality OCR service with multi-language support and document conversion capabilities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_api_key(api_key: str = Header(..., alias=config.settings.API_KEY_NAME)):
    if api_key != config.settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

@app.post("/process/file")
async def process_single_file(
    file: UploadFile = File(...),
    operation: str = Form(...),
    language: str = Form(config.settings.DEFAULT_LANGUAGE),
    core_count: int = Form(config.settings.DEFAULT_CORE_COUNT),
    api_key: str = Header(..., alias=config.settings.API_KEY_NAME)
):
    """
    Process a single file with the specified operation.
    Operations:
    - ocr: Perform OCR on PDF
    - pdf_to_word: Convert PDF to Word
    - word_to_pdf: Convert Word to PDF
    """
    verify_api_key(api_key)
    
    # Validate operation
    if operation not in ["ocr", "pdf_to_word", "word_to_pdf"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid operation"
        )
    
    # Validate language
    if language not in config.settings.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language. Supported languages: {', '.join(config.settings.SUPPORTED_LANGUAGES)}"
        )
    
    # Validate file size
    if file.size > config.settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {config.settings.MAX_FILE_SIZE/1024/1024}MB"
        )
    
    # Create unique directory for this request
    request_id = str(uuid.uuid4())
    input_dir = config.settings.UPLOAD_DIR / request_id
    output_dir = config.settings.OUTPUT_DIR / request_id
    input_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    
    try:
        # Save uploaded file
        input_path = input_dir / file.filename
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Determine output filename
        output_filename = input_path.stem
        if operation == "pdf_to_word":
            output_filename += ".docx"
        else:
            output_filename += ".pdf"
        output_path = output_dir / output_filename
        
        # Start processing task
        task = process_file.delay(
            str(input_path),
            str(output_path),
            operation,
            language,
            core_count
        )
        
        return {
            "task_id": task.id,
            "status": "processing",
            "message": "File processing started"
        }
    
    except Exception as e:
        # Clean up on error
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/process/directory")
async def process_directory_files(
    files: List[UploadFile] = File(...),
    operation: str = Form(...),
    language: str = Form(config.settings.DEFAULT_LANGUAGE),
    core_count: int = Form(config.settings.DEFAULT_CORE_COUNT),
    api_key: str = Header(..., alias=config.settings.API_KEY_NAME)
):
    """Process multiple files in a directory."""
    verify_api_key(api_key)
    
    # Validate operation
    if operation not in ["ocr", "pdf_to_word", "word_to_pdf"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid operation"
        )
    
    # Create unique directory for this request
    request_id = str(uuid.uuid4())
    input_dir = config.settings.UPLOAD_DIR / request_id
    output_dir = config.settings.OUTPUT_DIR / request_id
    input_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    
    try:
        # Save uploaded files
        for file in files:
            if file.size > config.settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} too large"
                )
            
            input_path = input_dir / file.filename
            with input_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        # Start processing task
        task = process_directory.delay(
            str(input_dir),
            str(output_dir),
            operation,
            language,
            core_count
        )
        
        return {
            "task_id": task.id,
            "status": "processing",
            "message": "Directory processing started"
        }
    
    except Exception as e:
        # Clean up on error
        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/task/{task_id}/progress")
async def check_task_progress(
    task_id: str,
    api_key: str = Header(..., alias=config.settings.API_KEY_NAME)
):
    """Get the progress of a processing task."""
    verify_api_key(api_key)
    
    task = process_file.AsyncResult(task_id)
    if task.ready():
        result = task.get()
        if result["status"] == "error":
            return {
                "status": "error",
                "error": result["error"],
                "progress": 100
            }
        return {
            "status": "completed",
            "result": result,
            "progress": 100
        }
    
    progress = get_task_progress(task_id)
    return {
        "status": "processing",
        "progress": progress["progress"],
        "message": progress["status"]
    }

@app.get("/task/{task_id}/download/{filename}")
async def download_processed_file(
    task_id: str,
    filename: str,
    api_key: str = Header(..., alias=config.settings.API_KEY_NAME)
):
    """Download a processed file."""
    verify_api_key(api_key)
    
    task = process_file.AsyncResult(task_id)
    if not task.ready():
        raise HTTPException(
            status_code=400,
            detail="Task not completed"
        )
    
    result = task.get()
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result["error"]
        )
    
    file_path = Path(result["output_path"])
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@app.on_event("startup")
async def startup_event():
    """Create necessary directories on startup."""
    config.settings.create_directories()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 