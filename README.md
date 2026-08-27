# EIL Audit Automation

Phase 1 implementation for the EIL Excel Inspection & Audit Processing internal web application.

## ⚠️ PHASE 1 LIMITATIONS
**PHASE 1 DOES NOT PERFORM AUDIT CALCULATIONS OR MODIFY EXCEL 3.**

This phase establishes the foundational architecture:
- Independent upload and validation of three Excel workbooks.
- Extraction of sheet metadata, column metadata, and data type inference.
- UI for inspecting the uploaded data in a read-only preview.

## Architecture & Technology Stack
- **Frontend**: React, TypeScript, Vite, Tailwind CSS (Desktop-first UI).
- **Backend**: Python, FastAPI, Pandas, OpenPyXL.
- **Storage**: Local filesystem storage (`storage/uploads`) for immutable workbooks.
- **Session**: In-memory session tracking.

## Directory Structure
```
eil-audit-automation/
├── frontend/       # Vite + React + TS Frontend
├── backend/        # FastAPI + Python Backend
├── storage/        
│   ├── uploads/    # Uploaded immutable source files
│   └── working/    # (Future) Modifiable copies
├── docker-compose.yml
└── README.md
```

## Local Setup & Startup

### Docker (Recommended)
You can start the entire stack using Docker Compose:
```bash
docker-compose up --build
```
The frontend will be available at `http://localhost:5173` and the backend at `http://localhost:8000`.

### Manual Startup
**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## How to Use
1. Open the frontend dashboard.
2. The system automatically creates a session.
3. Click on the upload slots for **Excel 1**, **Excel 2**, and **Excel 3** to upload your `.xlsx` files.
4. After successful uploads, click **Inspect Excel X** to load the workbook inspector.
5. The inspector will display all available sheets. Click a sheet to view row/column counts and a tabular preview of the data (with inferred data types).

## API Overview
- `GET /api/health` - Health check.
- `POST /api/sessions` - Creates a new processing session.
- `POST /api/sessions/{session_id}/files/{workbook_type}` - Uploads a workbook.
- `GET /api/sessions/{session_id}/workbooks/{workbook_type}` - Retrieves workbook metadata.
- `GET /api/sessions/{session_id}/workbooks/{workbook_type}/sheets/{sheet_name}` - Retrieves sheet preview and columns.

## Testing
To run the automated backend tests (which use synthetic `.xlsx` files):
```bash
cd backend
pytest tests/
```

## Planned Future Phases
- **Phase 2**: Column mapping UI.
- **Phase 3**: Job Number matching.
- **Phase 4-5**: Excel 1 & 2 business rules and inspection processing.
- **Phase 6**: Excel 3 calculation engine.
- **Phase 7**: Result/review screen with manual edits.
- **Phase 8**: Excel 3 workbook modification (editing the working copy while preserving original structure).
