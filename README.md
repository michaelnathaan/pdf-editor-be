# PDF Editor Service - Backend

A FastAPI-based microservice for editing PDF files with image insertion capabilities. Designed to integrate with document management systems like Teedy.

## 🚀 Features

- ✅ Upload PDF files
- ✅ Create editing sessions with expiration
- ✅ Add images to PDF pages (JPEG, PNG, GIF, WebP)
- ✅ Move, resize, rotate images on PDF
- ✅ Undo/Redo operations
- ✅ Save and download edited PDFs
- ✅ Session-based authentication
- ✅ Webhook notifications (for Teedy integration)
- ✅ RESTful API with automatic documentation

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 (Remote)
- **PDF Processing**: PyPDF2, ReportLab
- **Image Processing**: Pillow
- **Storage**: Local file system
- **Deployment**: Docker & Docker Compose

## 📋 Prerequisites

- Docker & Docker Compose
- PostgreSQL database (already configured remotely)
- Python 3.11+ (optional, for local development)

## ⚡ Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
cd pdf-editor-backend

# Copy environment file (if not already present)
cp .env.example .env

# Edit .env with your database credentials
```

### 2. Start the Service

```bash
# Build and start
docker-compose up --build -d

# Check logs
docker-compose logs -f backend

# Stop
docker-compose down
```

### 3. Verify It's Running

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","app":"PDF Editor Service","version":"1.0.0"}
```

### 4. Access API Documentation

Open in your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
pdf-editor-backend/
├── app/
│   ├── api/v1/              # API endpoints
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic schemas (validation)
│   ├── services/            # Business logic
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   └── main.py              # FastAPI app entry point
├── storage/                 # File storage
│   ├── uploads/             # Original PDFs
│   ├── edited/              # Edited PDFs
│   └── temp/                # Temporary session files
├── .env                     # Environment variables
├── docker-compose.yml       # Docker setup
├── Dockerfile               # Docker image
├── requirements.txt         # Python dependencies
└── README.md
```

## 🔑 Authentication

### Service-to-Service (Teedy → PDF Editor)

Use API key in `X-API-Key` header:

```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "X-API-Key: your-api-secret-key" \
  -F "file=@document.pdf"
```

### Browser/User (Frontend → PDF Editor)

Use session token in query parameter:

```bash
curl http://localhost:8000/api/v1/sessions/{session_id}/operations?session_token={token}
```

## 📡 API Endpoints

### File Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/files/upload` | Upload PDF file | API Key |
| GET | `/api/v1/files/{file_id}` | Get file info | API Key |
| GET | `/api/v1/files/{file_id}/download` | Download original PDF | API Key |
| DELETE | `/api/v1/files/{file_id}` | Delete file | API Key |

### Session Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/files/{file_id}/sessions` | Create edit session | API Key |
| GET | `/api/v1/files/{file_id}/sessions/{session_id}` | Get session info | Session Token |
| POST | `/api/v1/files/{file_id}/sessions/{session_id}/commit` | Save edited PDF | Session Token |
| GET | `/api/v1/sessions/{session_id}/download` | Download edited PDF | Session Token |

### Edit Operations (Undo/Redo)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/sessions/{session_id}/operations` | Add operation | Session Token |
| GET | `/api/v1/sessions/{session_id}/operations` | List all operations | Session Token |
| DELETE | `/api/v1/sessions/{session_id}/operations/{op_id}` | Delete operation | Session Token |
| DELETE | `/api/v1/sessions/{session_id}/operations` | Clear all operations | Session Token |

### Image Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/sessions/{session_id}/images` | Upload image | Session Token |
| GET | `/api/v1/sessions/{session_id}/images/{image_id}` | Get image | Session Token |
| DELETE | `/api/v1/sessions/{session_id}/images/{image_id}` | Delete image | Session Token |

## 🔄 Integration Flow with Teedy

```
1. User clicks "Edit PDF" in Teedy
   ↓
2. Teedy uploads PDF to editor service
   POST /api/v1/files/upload
   ↓
3. Teedy creates edit session
   POST /api/v1/files/{file_id}/sessions
   Response: { "editor_url": "...", "session_token": "..." }
   ↓
4. Teedy redirects user to editor_url
   ↓
5. User edits PDF in browser
   - Upload images
   - Position, resize, rotate
   - Undo/redo changes
   ↓
6. User clicks "Save"
   POST /api/v1/sessions/{session_id}/commit
   ↓
7. Editor service processes PDF and calls webhook
   POST {callback_url} with download link
   ↓
8. Teedy downloads edited PDF
   GET /api/v1/sessions/{session_id}/download
```

## 📝 Environment Variables

```env
# Application
APP_NAME="PDF Editor Service"
APP_VERSION=1.0.0
DEBUG=True
PORT=8000

# Security
API_SECRET_KEY=your-secret-key-here
SESSION_SECRET_KEY=your-session-secret

# Database (Remote PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
DATABASE_URL_SYNC=postgresql://user:pass@host:5432/dbname

# Storage
STORAGE_PATH=./storage
UPLOAD_MAX_SIZE=52428800  # 50MB

# Session
SESSION_EXPIRY_HOURS=24

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

## 📊 Operation Data Format

### Add Image Operation
```json
{
  "operation_type": "add_image",
  "operation_data": {
    "page": 1,
    "image_id": "uuid",
    "image_path": "/storage/temp/session-id/image.png",
    "position": {"x": 100, "y": 200, "width": 300, "height": 200},
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

## 🎯 Roadmap

- [ ] Frontend React application
- [ ] Real-time collaboration
- [ ] Text annotation support
- [ ] Digital signatures
- [ ] Page manipulation (add/delete/reorder)
- [ ] Batch processing
- [ ] OCR text recognition