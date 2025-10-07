# PDF Editor Service

A FastAPI-based service for editing PDF files with image insertion capabilities. Designed to integrate with document management systems like Teedy.

## Features

- ✅ Upload PDF files
- ✅ Create editing sessions with expiration
- ✅ Add images to PDF pages
- ✅ Move, resize, rotate images
- ✅ Undo/Redo operations
- ✅ Save and download edited PDFs
- ✅ Session-based authentication
- ✅ Webhook notifications (for Teedy integration)
- ✅ RESTful API

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **PDF Processing**: PyPDF2, ReportLab
- **Image Processing**: Pillow
- **Storage**: Local file system
- **Deployment**: Docker & Docker Compose

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15 (if running without Docker)

## API Endpoints

### File Management

- `POST /api/v1/files/upload` - Upload a PDF file
- `GET /api/v1/files/{file_id}` - Get file information
- `GET /api/v1/files/{file_id}/download` - Download original PDF
- `DELETE /api/v1/files/{file_id}` - Delete file

### Session Management

- `POST /api/v1/files/{file_id}/sessions` - Create edit session
- `GET /api/v1/files/{file_id}/sessions/{session_id}` - Get session info
- `POST /api/v1/files/{file_id}/sessions/{session_id}/commit` - Save edited PDF
- `GET /api/v1/sessions/{session_id}/download` - Download edited PDF

### Edit Operations

- `POST /api/v1/sessions/{session_id}/operations` - Add operation
- `GET /api/v1/sessions/{session_id}/operations` - List operations
- `DELETE /api/v1/sessions/{session_id}/operations/{operation_id}` - Delete operation
- `DELETE /api/v1/sessions/{session_id}/operations` - Clear all operations

### Image Management

- `POST /api/v1/sessions/{session_id}/images` - Upload image
- `GET /api/v1/sessions/{session_id}/images/{image_id}` - Get image
- `DELETE /api/v1/sessions/{session_id}/images/{image_id}` - Delete image

## Authentication

### Service-to-Service (Teedy → PDF Editor)

Use API key in header:
```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "X-API-Key: your-api-secret-key" \
  -F "file=@document.pdf"
```

### Browser/User (Frontend → PDF Editor)

Use session token:
```bash
curl http://localhost:8000/api/v1/sessions/{session_id}/operations?session_token={token}
```

## Integration with Teedy

### Flow

1. User clicks "Edit PDF" in Teedy
2. Teedy uploads PDF to editor service:
   ```bash
   POST /api/v1/files/upload
   ```
3. Teedy creates edit session:
   ```bash
   POST /api/v1/files/{file_id}/sessions
   {
     "callback_url": "https://teedy.example.com/api/webhook/pdf-edited"
   }
   ```
4. Teedy redirects user to `editor_url`
5. User edits PDF in browser
6. User saves → Editor service calls Teedy webhook
7. Teedy downloads edited PDF:
   ```bash
   GET /api/v1/sessions/{session_id}/download?token={token}
   ```

### Webhook Payload

When editing is complete, the service sends:
```json
{
  "session_id": "uuid",
  "file_id": "uuid",
  "status": "completed",
  "download_url": "https://editor.example.com/api/v1/sessions/{session_id}/download?token={token}",
  "completed_at": "2025-10-07T10:30:00Z"
}
```

## Operation Data Format

### Add Image Operation
```json
{
  "operation_type": "add_image",
  "operation_data": {
    "page": 1,
    "image_id": "uuid",
    "image_path": "/storage/temp/session-id/image.png",
    "position": {
      "x": 100,
      "y": 200,
      "width": 300,
      "height": 200
    },
    "rotation": 0,
    "opacity": 1.0
  }
}
```

### Move Image Operation
```json
{
  "operation_type": "move_image",
  "operation_data": {
    "page": 1,
    "image_id": "uuid",
    "old_position": {"x": 100, "y": 200},
    "new_position": {"x": 150, "y": 250}
  }
}
```

## Project Structure

```
pdf-editor-backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── config.py        # Configuration
│   ├── database.py      # Database setup
│   └── main.py          # FastAPI app
├── storage/             # File storage
├── docker-compose.yml   # Docker setup
└── requirements.txt     # Python dependencies
```

## Support

For issues and questions, please create an issue in the repository.