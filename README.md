# Advanced OCR Service

A high-performance OCR service with multi-language support, document conversion capabilities, and progress tracking. This service is designed to work seamlessly with frontend applications and provides a robust API for document processing.

## Features

- PDF OCR with multi-language support
- PDF to Word conversion
- Word to PDF conversion
- Batch processing support (process entire directories)
- Real-time progress tracking
- Configurable processing cores
- Queue system for handling multiple requests
- API key authentication
- High-quality OCR results

## Supported Languages

- Indonesia (ind)
- English (eng)
- French (fra)
- German (deu)
- Spanish (spa)
- Italian (ita)
- Portuguese (por)
- Russian (rus)
- Simplified Chinese (chi_sim)
- Traditional Chinese (chi_tra)
- Japanese (jpn)
- Korean (kor)
- Arabic (ara)
- Hindi (hin)

## Prerequisites

- Python 3.8+
- Redis server
- Tesseract OCR
- System dependencies for PDF processing

### Installing System Dependencies

For Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
sudo apt-get install -y tesseract-ocr-all
sudo apt-get install -y poppler-utils
```

For CentOS/RHEL:
```bash
sudo yum install -y tesseract
sudo yum install -y tesseract-langpack-*
sudo yum install -y poppler-utils
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ocr-service
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
```

5. Update the `.env` file with your configuration:
```env
API_KEY=your-secret-api-key
REDIS_HOST=localhost
REDIS_PORT=6379
DEFAULT_CORE_COUNT=1
```

## Running the Service

1. Start Redis server:
```bash
redis-server
```

2. Start Celery worker:
```bash
celery -A ocr_service.queue.task_queue worker --loglevel=info
```

3. Start the FastAPI server:
```bash
uvicorn ocr_service.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Process Single File
```http
POST /process/file
Content-Type: multipart/form-data
X-API-Key: your-api-key

Parameters:
- file: File (required)
- operation: string (required) - "ocr", "pdf_to_word", or "word_to_pdf"
- language: string (optional) - Default: "ind"
- core_count: integer (optional) - Default: 1
```

### Process Directory
```http
POST /process/directory
Content-Type: multipart/form-data
X-API-Key: your-api-key

Parameters:
- files: List[File] (required)
- operation: string (required) - "ocr", "pdf_to_word", or "word_to_pdf"
- language: string (optional) - Default: "eng"
- core_count: integer (optional) - Default: 1
```

### Check Task Progress
```http
GET /task/{task_id}/progress
X-API-Key: your-api-key
```

### Download Processed File
```http
GET /task/{task_id}/download/{filename}
X-API-Key: your-api-key
```

## Integration with Frontend

The service is designed to work with Vue.js frontend applications. Here's an example of how to integrate:

```javascript
// Example Vue.js code for file upload and progress tracking
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('operation', 'ocr');
  formData.append('language', 'eng');
  
  const response = await fetch('http://your-server:8000/process/file', {
    method: 'POST',
    headers: {
      'X-API-Key': 'your-api-key'
    },
    body: formData
  });
  
  const { task_id } = await response.json();
  
  // Poll for progress
  const interval = setInterval(async () => {
    const progressResponse = await fetch(`http://your-server:8000/task/${task_id}/progress`, {
      headers: {
        'X-API-Key': 'your-api-key'
      }
    });
    
    const progress = await progressResponse.json();
    
    if (progress.status === 'completed') {
      clearInterval(interval);
      // Download the processed file
      window.location.href = `http://your-server:8000/task/${task_id}/download/processed_file.pdf`;
    }
  }, 1000);
}
```

## Error Handling

The service provides detailed error messages for various scenarios:
- Invalid API key
- Unsupported file format
- File size too large
- Invalid operation
- Unsupported language
- Processing errors

## Performance Optimization

The service is optimized for performance:
- Multi-core processing support
- Queue system for handling multiple requests
- Efficient memory management
- Temporary file cleanup
- Progress tracking with minimal overhead

## Security Considerations

- API key authentication required for all endpoints
- Temporary file cleanup after processing
- Input validation and sanitization
- File size limits
- Secure file handling

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

MIT License 