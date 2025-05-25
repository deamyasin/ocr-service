import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
from pathlib import Path
from typing import List, Dict, Optional
import tempfile
from pdf2docx import Converter
from docx2pdf import convert
import shutil
from tqdm import tqdm
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import config

class OCRProcessor:
    def __init__(self, core_count: int = config.settings.DEFAULT_CORE_COUNT):
        self.core_count = min(core_count, config.settings.MAX_CORE_COUNT)
        self._progress = {}
        self._progress_lock = threading.Lock()

    def _update_progress(self, task_id: str, progress: float, status: str = ""):
        with self._progress_lock:
            self._progress[task_id] = {"progress": progress, "status": status}

    def get_progress(self, task_id: str) -> Dict:
        with self._progress_lock:
            return self._progress.get(task_id, {"progress": 0, "status": "Not started"})

    def ocr_pdf(self, input_path: Path, output_path: Path, language: str = "eng", task_id: str = None) -> Path:
        """Perform OCR on PDF and create searchable PDF."""
        if not task_id:
            task_id = str(input_path)

        self._update_progress(task_id, 0, "Converting PDF to images")
        
        # Convert PDF to images
        images = convert_from_path(str(input_path), dpi=config.settings.OCR_DPI)
        total_pages = len(images)
        
        # Process each page with OCR
        with ThreadPoolExecutor(max_workers=self.core_count) as executor:
            futures = []
            for page_num, image in enumerate(images, 1):
                future = executor.submit(
                    self._process_page,
                    image,
                    language,
                    page_num,
                    total_pages,
                    task_id
                )
                futures.append(future)

            # Collect results
            pdf_pages = []
            for future in as_completed(futures):
                pdf_page = future.result()
                pdf_pages.append(pdf_page)

        # Combine pages and save
        self._update_progress(task_id, 95, "Combining pages")
        pdf_pages[0].save(
            output_path,
            save_all=True,
            append_images=pdf_pages[1:],
            resolution=config.settings.OCR_DPI
        )
        
        self._update_progress(task_id, 100, "Complete")
        return output_path

    def _process_page(self, image: Image, language: str, page_num: int, total_pages: int, task_id: str) -> Image:
        """Process a single page with OCR."""
        progress = (page_num - 1) / total_pages * 100
        self._update_progress(
            task_id,
            progress,
            f"Processing page {page_num}/{total_pages}"
        )
        
        # Enhance image quality for better OCR
        image = self._enhance_image(image)
        
        # Perform OCR
        text = pytesseract.image_to_pdf_or_hocr(
            image,
            extension='pdf',
            lang=language
        )
        
        # Convert back to image for PDF creation
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(text)
            temp_pdf.flush()
            result_image = convert_from_path(temp_pdf.name)[0]
            os.unlink(temp_pdf.name)
        
        return result_image

    def _enhance_image(self, image: Image) -> Image:
        """Enhance image quality for better OCR results."""
        # Convert to grayscale
        image = image.convert('L')
        
        # Increase contrast
        image = image.point(lambda x: 0 if x < 128 else 255, '1')
        
        return image

    def pdf_to_word(self, input_path: Path, output_path: Path, task_id: str = None) -> Path:
        """Convert PDF to Word document."""
        if not task_id:
            task_id = str(input_path)

        self._update_progress(task_id, 0, "Starting PDF to Word conversion")
        
        cv = Converter(str(input_path))
        cv.convert(str(output_path), start=0, end=None)
        cv.close()
        
        self._update_progress(task_id, 100, "Complete")
        return output_path

    def word_to_pdf(self, input_path: Path, output_path: Path, task_id: str = None) -> Path:
        """Convert Word document to PDF."""
        if not task_id:
            task_id = str(input_path)

        self._update_progress(task_id, 0, "Starting Word to PDF conversion")
        
        convert(str(input_path), str(output_path))
        
        self._update_progress(task_id, 100, "Complete")
        return output_path

    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        operation: str,
        language: str = "eng",
        task_id: str = None
    ) -> List[Path]:
        """Process all supported files in a directory."""
        if not task_id:
            task_id = str(input_dir)

        input_files = [
            f for f in input_dir.iterdir()
            if f.suffix.lower() in config.settings.SUPPORTED_INPUT_FORMATS
        ]
        
        if not input_files:
            return []

        output_files = []
        total_files = len(input_files)
        
        for idx, input_file in enumerate(input_files, 1):
            progress = (idx - 1) / total_files * 100
            self._update_progress(
                task_id,
                progress,
                f"Processing file {idx}/{total_files}: {input_file.name}"
            )
            
            output_file = output_dir / f"{input_file.stem}_processed{input_file.suffix}"
            
            if operation == "ocr":
                self.ocr_pdf(input_file, output_file, language, f"{task_id}_{idx}")
            elif operation == "pdf_to_word":
                self.pdf_to_word(input_file, output_file, f"{task_id}_{idx}")
            elif operation == "word_to_pdf":
                self.word_to_pdf(input_file, output_file, f"{task_id}_{idx}")
            
            output_files.append(output_file)

        self._update_progress(task_id, 100, "Complete")
        return output_files 