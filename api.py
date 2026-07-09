from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import os
import re
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from dotenv import load_dotenv, set_key, dotenv_values

# Path to scripts/service_account.json
BASE_DIR = os.path.dirname(__file__)
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'scripts', 'service_account.json')
DOTENV_PATH = os.path.join(BASE_DIR, 'scripts', '.env')

def _open_worksheet(sheet_url: str | None = None):
    """Open a worksheet using the service account. If sheet_url is None, uses REGISTRATION_SHEET_URL."""
    sheet_url = sheet_url or os.getenv('REGISTRATION_SHEET_URL')
    if not sheet_url:
        raise RuntimeError('REGISTRATION_SHEET_URL not configured')

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(sheet_url)

    # If gid provided use matching worksheet else first
    gid_match = re.search(r'gid=([0-9]+)', sheet_url)
    if gid_match:
        target_gid = int(gid_match.group(1))
        for sheet in spreadsheet.worksheets():
            if sheet.id == target_gid:
                return sheet
    return spreadsheet.get_worksheet(0)


app = FastAPI(title="SwipeGen-Automation API")


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.get("/info")
async def info():
    return JSONResponse({
        "project": "SwipeGen-Automation",
        "description": "Automation toolkit for recruitment workflows",
    })


# Example trigger endpoint (safe placeholder)
# Extend this to call existing script functions with proper authentication and validation.
@app.post("/trigger/{task}")
async def trigger_task(task: str):
    # Do NOT execute arbitrary shell commands here.
    # Map allowed task names to internal functions if needed.
    allowed = {"generate_offers": "Generate offer letters", "generate_certificates": "Generate certificates"}
    if task not in allowed:
        return JSONResponse({"error": "unknown task"}, status_code=400)
    return JSONResponse({"task": task, "status": "accepted", "description": allowed[task]})


# ── Candidates / Sheet endpoints used by frontend
@app.get("/api/health")
async def api_health():
    return JSONResponse({"status": "ok"})


@app.get("/api/candidates")
async def list_candidates(status: str = None, search: str = None):
    try:
        ws = _open_worksheet()
        records = ws.get_all_records()
        result = []
        for i, row in enumerate(records, start=2):
            r = dict(row)
            r['_row'] = i
            r['id'] = i
            result.append(r)

        if status:
            result = [r for r in result if (r.get('Status') or '').strip() == status]
        if search:
            q = search.lower()
            result = [r for r in result if q in str(r.get('Name','')).lower() or q in str(r.get('Email','')).lower()]

        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/candidates/{row_id}")
async def get_candidate(row_id: int):
    try:
        ws = _open_worksheet()
        row = ws.row_values(row_id)
        headers = ws.row_values(1)
        padded = row + [''] * (len(headers) - len(row))
        data = dict(zip(headers, padded))
        data['_row'] = row_id
        data['id'] = row_id
        return JSONResponse(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/candidates/{row_id}/status")
async def update_candidate_status(row_id: int, payload: dict):
    try:
        status = payload.get('status')
        if not status:
            raise HTTPException(status_code=400, detail='status required')
        ws = _open_worksheet()
        headers = ws.row_values(1)
        # Find status column index (1-based)
        try:
            idx = next(i for i, h in enumerate(headers, 1) if h.strip().lower() == 'status')
        except StopIteration:
            idx = len(headers) + 1
            # extend header? just write to guessed column

        ws.update_cell(row_id, idx, status)
        return JSONResponse({'success': True, 'row': row_id, 'status': status})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/candidates")
async def create_candidate(payload: dict):
    """Append a new candidate row to the registration sheet.

    Expected payload keys: name, email, college, role, cgpa, resume_link
    Returns the created row number as `id`.
    """
    try:
        ws = _open_worksheet()
        headers = ws.row_values(1)

        # Map incoming payload fields to sheet columns
        mapping = {
            'name': 'Name',
            'email': 'Email',
            'college': 'College',
            'role': 'Role',
            'cgpa': 'CGPA',
            'resume_link': 'Resume Link',
        }

        # Build row in header order
        row_values = []
        for h in headers:
            key = None
            for k, v in mapping.items():
                if v.lower() == h.strip().lower():
                    key = k
                    break
            if key:
                row_values.append(payload.get(key, ''))
            else:
                # For other columns, leave blank except for Status/Applied Date
                if h.strip().lower() == 'status':
                    row_values.append('applied')
                elif h.strip().lower() in ('applied date', 'applieddate'):
                    from datetime import datetime
                    row_values.append(datetime.utcnow().isoformat())
                else:
                    row_values.append('')

        # If headers were missing expected columns, append missing values at end
        # (gspread will expand as needed)
        append_result = ws.append_row(row_values)

        # gspread's append_row does not directly return row index; fetch last row
        last_row = len(ws.get_all_values())
        created = {
            'id': last_row,
            **{k: payload.get(k, '') for k in mapping.keys()}
        }
        created['_row'] = last_row
        return JSONResponse(created)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/settings')
async def get_settings():
    """Return current configurable settings (sheet URLs and ids)."""
    # Load .env values if present
    load_dotenv(DOTENV_PATH)
    keys = [
        'REGISTRATION_SHEET_URL', 'INTERVIEW_RESPONSE_SHEET_URL', 'OFFER_DETAILS_SHEET_URL',
        'CERTIFICATES_DRIVE_FOLDER_ID', 'OFFER_LETTERS_DRIVE_FOLDER_ID', 'COMPANY_NAME',
        'SENDER_EMAIL', 'SMTP_PORT'
    ]
    values = {k: os.getenv(k) for k in keys}
    return JSONResponse(values)


@app.post('/api/settings')
async def set_settings(payload: dict):
    """Update settings by writing to scripts/.env. Returns updated values."""
    try:
        # Read existing dotenv values
        current = dotenv_values(DOTENV_PATH) or {}
        for k, v in payload.items():
            # Only allow known keys to be set
            if k.startswith('REGISTRATION_') or k.endswith('_SHEET_URL') or k in ('COMPANY_NAME', 'SENDER_EMAIL', 'SMTP_PORT', 'CERTIFICATES_DRIVE_FOLDER_ID', 'OFFER_LETTERS_DRIVE_FOLDER_ID'):
                set_key(DOTENV_PATH, k, str(v))
        # Reload into environment
        load_dotenv(DOTENV_PATH, override=True)
        return await get_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/settings/test-sheet')
async def test_sheet(payload: dict):
    """Test connection to a given Google Sheet URL. Payload: {"sheet_url": "..."} or uses REGISTRATION_SHEET_URL."""
    try:
        sheet_url = payload.get('sheet_url') if payload else None
        ws = _open_worksheet(sheet_url)
        # return sheet title and first-row headers
        headers = ws.row_values(1)
        return JSONResponse({'ok': True, 'title': ws.title, 'headers': headers})
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=400)
