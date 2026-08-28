# EIL Audit Automation

The EIL Excel Inspection & Audit Processing internal web application.

## Architecture & Technology Stack
- **Frontend**: React, TypeScript, Vite, Tailwind CSS (Desktop-first UI).
- **Backend**: Python, FastAPI, Pandas, OpenPyXL.
- **Storage**: Local filesystem storage (`storage/`) for immutable workbooks and generated outputs.
- **Session**: In-memory session tracking.

## Prerequisites
To run the application, you only need the following installed on your machine:
- **Docker**
- **Docker Compose**

*Note: The production compose file uses prebuilt Docker Hub images. Therefore, you do not need Python, Node.js, npm, or a local virtual environment to run the application.*

## Production Deployment

The intended workflow for a new user to start the application is:

1. Clone or download this repository.
2. Navigate to the project root directory.
3. Create the required storage directory on your host machine.
4. Pull the latest images and start the containers.

```bash
# 1. Create the persistent storage directory
mkdir -p storage

# 2. Pull the prebuilt images from Docker Hub
docker compose -f docker-compose.prod.yml pull

# 3. Start the application in the background
docker compose -f docker-compose.prod.yml up -d
```

### Current Image Versions
The `docker-compose.prod.yml` uses the following Docker Hub images:
- `sandarsh/eil-backend:v1.2.0`
- `sandarsh/eil-frontend:v1.2.0`

### Application URLs

Once the containers are running, you can access the application at:
- **Frontend**: http://localhost:5173
- **Backend (API Docs)**: http://localhost:8000/docs

### Persistent Storage
The `storage/` directory is mounted from the host machine into the backend container. This ensures that any uploaded Excel files and generated audit outputs persist across container recreation and restarts.

### Useful Commands

Check the status of the running containers:
```bash
docker compose -f docker-compose.prod.yml ps
```

View the logs of the application:
```bash
docker compose -f docker-compose.prod.yml logs
```

Stop the application:
```bash
docker compose -f docker-compose.prod.yml down
```

## Running Locally for Development

If you wish to develop or modify the source code, you can start the entire stack building directly from the source:
```bash
docker compose up -d --build
```

**Manual Startup**:

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
1. Open the frontend dashboard at `http://localhost:5173`.
2. The system automatically creates a session.
3. Upload the required **Excel 1**, **Excel 2**, and **Excel 3** `.xlsx` files.
4. Proceed to the Mapping Step to align the column headers.
5. Process the jobs to view the Analysis Dashboard and Review screens.
6. Generate and download the final audit output Excel file.

## Testing
To run the automated E2E tests:
```bash
./run_e2e.sh
```

To run the backend unit tests:
```bash
cd backend
pytest tests/
```
