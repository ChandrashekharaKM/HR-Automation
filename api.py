from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import os
import re
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Path to scripts/service_account.json
BASE_DIR = os.path.dirname(__file__)
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'scripts', 'service_account.json')

def _open_worksheet():
    sheet_url = os.getenv('REGISTRATION_SHEET_URL')
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
