from celery import Celery
from pathlib import Path
from typing import Dict, Optional
import uuid
from ocr_service.processors.ocr_processor import OCRProcessor
from ocr_service.config import settings

# Initialize Celery
celery_app = Celery(
    'ocr_tasks',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task(bind=True)
def process_file(
    self,
    input_path: str,
    output_path: str,
    operation: str,
    language: str = "eng",
    core_count: int = settings.DEFAULT_CORE_COUNT
) -> Dict:
    """Process a single file with progress tracking."""
    processor = OCRProcessor(core_count=core_count)
    task_id = str(self.request.id)
    
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    try:
        if operation == "ocr":
            processor.ocr_pdf(input_path, output_path, language, task_id)
        elif operation == "pdf_to_word":
            processor.pdf_to_word(input_path, output_path, task_id)
        elif operation == "word_to_pdf":
            processor.word_to_pdf(input_path, output_path, task_id)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return {
            "status": "success",
            "output_path": str(output_path),
            "task_id": task_id
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "task_id": task_id
        }

@celery_app.task(bind=True)
def process_directory(
    self,
    input_dir: str,
    output_dir: str,
    operation: str,
    language: str = "eng",
    core_count: int = settings.DEFAULT_CORE_COUNT
) -> Dict:
    """Process all files in a directory with progress tracking."""
    processor = OCRProcessor(core_count=core_count)
    task_id = str(self.request.id)
    
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    try:
        output_files = processor.process_directory(
            input_dir,
            output_dir,
            operation,
            language,
            task_id
        )
        
        return {
            "status": "success",
            "output_files": [str(f) for f in output_files],
            "task_id": task_id
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "task_id": task_id
        }

def get_task_progress(task_id: str) -> Dict:
    """Get the progress of a task."""
    processor = OCRProcessor()
    return processor.get_progress(task_id) 