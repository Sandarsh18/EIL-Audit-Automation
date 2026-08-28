# EIL Audit Automation

The EIL Excel Inspection & Audit Processing application is an automated, end-to-end data pipeline designed to consolidate, analyze, and generate master auditing reports from multiple source workbooks.

## Architecture & Technology Stack
- **Frontend**: React, TypeScript, Vite, Tailwind CSS (Desktop-first interactive UI).
- **Backend**: Python, FastAPI, Pandas, OpenPyXL (High-performance calculation engine).
- **Storage**: Local filesystem storage (`storage/`) with Docker volume mapping for persistent immutable workbooks and generated outputs.
- **Session State**: UUID-based session tracking for secure, isolated multi-step workflows.

---

## The Workflow (Step-by-Step)

The application utilizes a guided 6-step workflow to safely process inputs and generate outputs.

### Step 1: Upload (Source Workbooks)
The system requires three specific Excel workbooks to function:
- **Excel 1 (Consolidated Report)**: Contains the running orders, balances, and OCS completion dates.
- **Excel 2 (Inspection Call Log)**: Contains the raw inspection dates, working days, QAP values, and received dates.
- **Excel 3 (Master Template)**: The master Job Number list and the template structure used for the final output generation.

*All uploaded files are stored immutably on the backend.*

### Step 2: Inspect & Map Columns
Because column headers can vary between source files, this step allows you to map internal logical fields to the actual headers found in your uploaded workbooks. 
- You can dynamically inspect the available sheets and data within the browser.
- Select the precise target sheet and map required fields (e.g., Job Number, Balance Quantity, OCS Date, Inspection From/Upto).

### Step 3: Select Jobs
The backend reads **Excel 3** and extracts all unique Job Numbers based on your mapping. You can select specific jobs to analyze or process the entire batch.

### Step 4: Rule Analysis
This is where the calculation engine runs. 
- You must select an **Evaluation Month** (e.g., August 2026). 
- The engine processes the records in Excel 1 and Excel 2 based on strict business rules (see [Calculation Rules](#calculation-rules) below).
- Diagnostic panels display exact lineage, allowing you to trace exactly how a calculation was derived, or why a record was excluded.

### Step 5: Review & Approve
The Review Dashboard presents the calculated values (FD, Running Orders, OCS Done, Expediting, Inspection, Others, and Total). 
- **Non-zero highlighting**: Important numeric values > 0 are visually highlighted.
- **Manual Overrides**: You can manually edit any calculated value if human intervention is required.
- **Approval**: You must formally "Approve" a row. Only approved rows are passed to the final output. You can "Undo" approvals at any time before generating the output.

### Step 6: Generate Output
The backend takes your original **Excel 3 Master Template** and generates a pristine, customized `CONSOLIDATED_Manhour_Automated.xlsx` workbook:
- It strips out unused sheets.
- It dynamically updates string dates in the template (e.g., `for Mar'26` becomes `for Aug'26` based on the Evaluation Month).
- It injects only the **Approved** job rows, preserving the native Excel styling (fonts, borders, colors) of the template.
- It dynamically appends a "Leave" row and a "Total" row.
- It automatically inserts native `=SUM()` formulas into the Total row for dynamic spreadsheet behavior.
- **Custom Columns**: You can optionally define and append custom textual columns to the output.

---

## Calculation Rules & Excel Logic

The core value of the platform is the deterministic extraction and aggregation of data from the source workbooks.

### Excel 1 (Consolidated Report)
Excel 1 is evaluated on a strict 6-month historical window (5 months prior to the Evaluation Month + the Evaluation Month itself).
- **FD**: Counted if `Balance Quantity == 0` AND `OCS Date` is strictly blank.
- **OCS Done**: Counted if `Balance Quantity == 0` AND `OCS Date` is present and falls within the 6-month window.
- **Running Orders**: Counted if `Balance Quantity != 0`.

*Records with an OCS Date falling entirely outside the 6-month evaluation window are EXCLUDED from aggregation.*

### Excel 2 (Inspection Call Log)
Excel 2 calculations rely on dynamic mapping (typically mapped to columns like L and M for Inspection Dates).
- **Inspection (Days)**: Calculated by looking at the `Inspection From` and `Inspection Upto` dates. 
  - Formula: `(Upto Date - From Date) + 1` day. 
  - *Critical Constraint*: The dates must occur *strictly* within the chosen Evaluation Month. Dates in other months are excluded.
- **Others**: Looks at the `Date Received`. If the received date is within the 6-month window, it extracts the value from `QAP Appl.`. If `QAP Appl.` is blank, it falls back to the `Working Days` column.

### Combined Total Formula
The final calculated output combines the derivations:
1. **Expediting** = `(Running Orders + OCS Done) * 2`
2. **Total** = `Expediting + Inspection (from Excel 2) + Others (from Excel 2)`

---

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

---

## Local Development & Source Building

If you wish to develop or modify the source code, you can start the entire stack building directly from the source:
```bash
docker compose up -d --build
```

**Testing:**
To run the automated Playwright E2E UI workflow tests (Requires backend to be running):
```bash
./run_e2e.sh
```

To run the backend Python unit and integration tests (validating the core calculation engine):
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/
```
