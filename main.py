"""
HR Admin Portal — FastAPI Backend
==================================
Bridges the React frontend to the existing Python automation scripts.
Each endpoint calls the corresponding script logic directly.

Run with:
    pip install fastapi uvicorn python-dotenv gspread oauth2client
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

import os
import re
import json
import time
import smtplib
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import gspread
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv, set_key
from oauth2client.service_account import ServiceAccountCredentials
import sys

# ─── Setup ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
sys.path.append(str(SCRIPTS_DIR))
ENV_FILE   = SCRIPTS_DIR / ".env"
SA_FILE    = SCRIPTS_DIR / "service_account.json"
SENT_LOG   = SCRIPTS_DIR / "sent_history.json"

load_dotenv(ENV_FILE)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HR Admin Portal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Google Sheets helper ─────────────────────────────────────────────────────
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

_gspread_client = None
_cached_worksheet = None
_cached_url = None
_cached_ws_time = 0

_cached_sheet_values = None
_cached_sheet_time = 0
_cached_sheet_url = None

def clear_data_cache():
    global _cached_sheet_values, _cached_sheet_time, _cached_sheet_url, _cached_worksheet, _cached_url, _cached_ws_time
    _cached_sheet_values = None
    _cached_sheet_time = 0
    _cached_sheet_url = None
    _cached_worksheet = None
    _cached_url = None
    _cached_ws_time = 0

def get_client() -> gspread.Client:
    global _gspread_client
    if _gspread_client is not None:
        return _gspread_client
    if not SA_FILE.exists():
        raise HTTPException(500, "service_account.json not found in scripts/")
    creds = ServiceAccountCredentials.from_json_keyfile_name(str(SA_FILE), SCOPE)
    _gspread_client = gspread.authorize(creds)
    return _gspread_client

def open_sheet(url: str) -> gspread.Worksheet:
    global _cached_worksheet, _cached_url, _cached_ws_time
    if not url:
        raise HTTPException(400, "Sheet URL is not configured. Set it in Settings.")
    
    now = time.time()
    if _cached_worksheet is not None and _cached_url == url and (now - _cached_ws_time) < 4:
        return _cached_worksheet
        
    client = get_client()
    spreadsheet = client.open_by_url(url)
    gid_match = re.search(r"gid=([0-9]+)", url)
    
    target_sheet = None
    if gid_match:
        target_gid = int(gid_match.group(1))
        for ws in spreadsheet.worksheets():
            if ws.id == target_gid:
                target_sheet = ws
                break
                
    if not target_sheet:
        target_sheet = spreadsheet.get_worksheet(0)
        
    _cached_worksheet = target_sheet
    _cached_url = url
    _cached_ws_time = now
    return target_sheet

def get_sheet_values(url: str) -> list:
    global _cached_sheet_values, _cached_sheet_time, _cached_sheet_url
    now = time.time()
    if _cached_sheet_values is not None and _cached_sheet_url == url and (now - _cached_sheet_time) < 4:
        return _cached_sheet_values
        
    ws = open_sheet(url)
    values = ws.get_all_values()
    _cached_sheet_values = values
    _cached_sheet_time = now
    _cached_sheet_url = url
    return values

def get_sheet_records_from_values(values: list) -> list:
    if not values:
        return []
    headers = [h.strip() for h in values[0]]
    records = []
    for row in values[1:]:
        padded = row + [""] * (len(headers) - len(row))
        records.append(dict(zip(headers, padded)))
    return records

def find_col(headers: list, *keywords: str) -> Optional[int]:
    """Return 1-based column index matching all keywords (case-insensitive)."""
    for i, h in enumerate(headers, 1):
        h_lower = str(h).lower()
        if all(kw in h_lower for kw in keywords):
            return i
    return None

def log_activity(action_type: str, message: str):
    log = []
    if SENT_LOG.exists():
        try:
            log = json.loads(SENT_LOG.read_text())
        except Exception:
            log = []
    log.insert(0, {
        "id":   f"a{int(time.time()*1000)}",
        "time": datetime.now().strftime("%I:%M %p"),
        "type": action_type,
        "message": message,
        "icon": {"shortlist":"⭐","interview":"📧","hired":"✅","offer":"✉️","certificate":"🎓","docs":"📩"}.get(action_type, "📌"),
    })
    SENT_LOG.write_text(json.dumps(log[:100], indent=2))

# ─── Pydantic models ──────────────────────────────────────────────────────────
class SettingsUpdate(BaseModel):
    registration_sheet_url:       Optional[str] = None
    interview_response_sheet_url: Optional[str] = None
    offer_details_sheet_url:      Optional[str] = None
    sender_email:                 Optional[str] = None
    sender_password:              Optional[str] = None
    smtp_port:                    Optional[str] = None
    company_name:                 Optional[str] = None
    website_url:                  Optional[str] = None
    certificates_drive_folder_id: Optional[str] = None
    offer_letters_drive_folder_id:Optional[str] = None
    email_signature:              Optional[str] = None

class StatusUpdate(BaseModel):
    status: str
    row: Optional[int] = None
    email: Optional[str] = None

class InterviewSchedule(BaseModel):
    candidate_email: str
    candidate_name:  str
    date:            str
    time:            str
    interviewer:     Optional[str] = ""
    meet_link:       Optional[str] = ""
    row:             Optional[int] = None

# ─── Settings endpoints ───────────────────────────────────────────────────────
@app.get("/api/settings")
def get_settings():
    load_dotenv(ENV_FILE, override=True)
    return {
        "registration_sheet_url":        os.getenv("REGISTRATION_SHEET_URL", ""),
        "interview_response_sheet_url":  os.getenv("INTERVIEW_RESPONSE_SHEET_URL", ""),
        "offer_details_sheet_url":       os.getenv("OFFER_DETAILS_SHEET_URL", ""),
        "sender_email":                  os.getenv("SENDER_EMAIL", ""),
        "sender_password":               "••••••••" if os.getenv("SENDER_PASSWORD") else "",
        "smtp_port":                     os.getenv("SMTP_PORT", "587"),
        "company_name":                  os.getenv("COMPANY_NAME", "SwipeGen Technologies"),
        "website_url":                   os.getenv("WEBSITE_URL", ""),
        "certificates_drive_folder_id":  os.getenv("CERTIFICATES_DRIVE_FOLDER_ID", ""),
        "offer_letters_drive_folder_id": os.getenv("OFFER_LETTERS_DRIVE_FOLDER_ID", ""),
        "email_signature":               os.getenv("EMAIL_SIGNATURE", "Regards,\nHR Team\nSwipeGen Technologies"),
        "offer_template":                os.getenv("OFFER_TEMPLATE_NAME", "Default (offer_template.docx)"),
        "cert_template":                 os.getenv("CERT_TEMPLATE_NAME", "Default (Completion_Certificate.docx)"),
    }

@app.post("/api/settings")
def save_settings(body: SettingsUpdate):
    mapping = {
        "registration_sheet_url":        "REGISTRATION_SHEET_URL",
        "interview_response_sheet_url":  "INTERVIEW_RESPONSE_SHEET_URL",
        "offer_details_sheet_url":       "OFFER_DETAILS_SHEET_URL",
        "sender_email":                  "SENDER_EMAIL",
        "sender_password":               "SENDER_PASSWORD",
        "smtp_port":                     "SMTP_PORT",
        "company_name":                  "COMPANY_NAME",
        "website_url":                   "WEBSITE_URL",
        "certificates_drive_folder_id":  "CERTIFICATES_DRIVE_FOLDER_ID",
        "offer_letters_drive_folder_id": "OFFER_LETTERS_DRIVE_FOLDER_ID",
        "email_signature":               "EMAIL_SIGNATURE",
    }
    updates = body.dict(exclude_none=True)
    for field, value in updates.items():
        env_key = mapping.get(field)
        if env_key and value and value != "••••••••":
            set_key(str(ENV_FILE), env_key, value)
    load_dotenv(ENV_FILE, override=True)
    return {"success": True, "message": "Settings saved to .env"}

@app.post("/api/settings/test-sheet")
def test_sheet_connection(body: dict):
    url = body.get("url", "")
    if not url:
        raise HTTPException(400, "URL is required")
    try:
        ws = open_sheet(url)
        headers = ws.row_values(1)
        return {
            "success": True,
            "sheet_name": ws.title,
            "row_count": ws.row_count,
            "columns": headers[:10],
        }
    except Exception as e:
        raise HTTPException(400, str(e))

class EmailTemplates(BaseModel):
    interview: Optional[str] = None
    offer: Optional[str] = None
    certificate: Optional[str] = None

@app.get("/api/settings/templates")
def get_templates():
    tpl_dir = SCRIPTS_DIR / "templates"
    interview = (tpl_dir / "interview_email_template.html").read_text(encoding="utf-8") if (tpl_dir / "interview_email_template.html").exists() else ""
    offer = (tpl_dir / "offer_email_template.html").read_text(encoding="utf-8") if (tpl_dir / "offer_email_template.html").exists() else ""
    certificate = (tpl_dir / "completion_email_template.html").read_text(encoding="utf-8") if (tpl_dir / "completion_email_template.html").exists() else ""
    return {"interview": interview, "offer": offer, "certificate": certificate}

@app.post("/api/settings/templates")
def save_templates(body: EmailTemplates):
    tpl_dir = SCRIPTS_DIR / "templates"
    tpl_dir.mkdir(exist_ok=True)
    if body.interview is not None:
        (tpl_dir / "interview_email_template.html").write_text(body.interview, encoding="utf-8")
    if body.offer is not None:
        (tpl_dir / "offer_email_template.html").write_text(body.offer, encoding="utf-8")
    if body.certificate is not None:
        (tpl_dir / "completion_email_template.html").write_text(body.certificate, encoding="utf-8")
    return {"success": True}

@app.post("/api/settings/templates/upload/{template_type}")
async def upload_template_file(template_type: str, file: UploadFile = File(...)):
    if template_type not in ["offer", "certificate"]:
        raise HTTPException(400, "Invalid template type. Must be 'offer' or 'certificate'")
    ext = Path(file.filename).suffix.lower()
    if ext != ".docx":
        raise HTTPException(400, "Only Word documents (.docx) are allowed as templates")
    try:
        output_dir = BASE_DIR / "scripts" / "templates"
        output_dir.mkdir(parents=True, exist_ok=True)
        if template_type == "offer":
            target_path = output_dir / "offer_template.docx"
            set_key(str(ENV_FILE), "OFFER_TEMPLATE_NAME", file.filename)
        else:
            target_path = output_dir / "Completion_Certificate.docx"
            set_key(str(ENV_FILE), "CERT_TEMPLATE_NAME", file.filename)
            
        with open(target_path, "wb") as buffer:
            buffer.write(await file.read())
            
        log_activity("settings", f"Uploaded new {template_type} template: {file.filename}")
        return {"success": True, "message": f"{template_type.capitalize()} template uploaded successfully"}
    except Exception as e:
        logger.error(f"upload_template_file error: {e}")
        raise HTTPException(500, str(e))

def _get_deterministic_score(name: str, email: str, role: str) -> int:
    import hashlib
    h = hashlib.md5(f"{name}:{email}:{role}".encode('utf-8')).hexdigest()
    score = 60 + (int(h[:4], 16) % 39)
    return score

def _get_deterministic_skills(role: str) -> list:
    r = str(role).lower()
    if "web" in r or "front" in r:
        return ["React", "JavaScript", "HTML/CSS"]
    elif "back" in r or "py" in r:
        return ["Python", "FastAPI", "SQL", "Docker"]
    elif "data" in r or "ml" in r or "ai" in r:
        return ["Python", "Machine Learning", "Pandas"]
    elif "design" in r or "ui" in r or "ux" in r:
        return ["Figma", "UI Design", "Wireframing"]
    else:
        return ["Java", "SQL", "Git"]

# ─── Candidates endpoints ─────────────────────────────────────────────────────
def _row_to_candidate(headers: list, row: list, row_idx: int) -> dict:
    padded = row + [""] * (len(headers) - len(row))
    d = dict(zip(headers, padded))
    f_name = d.get("Name") or d.get("Full Name") or d.get("First Name", "")
    l_name = d.get("Last Name", "")
    full_name = f"{f_name} {l_name}".strip() if f_name and l_name else f_name
    email = d.get("Email address") or d.get("Email", "")
    role = d.get("Role") or d.get("Position") or d.get("Domain") or d.get("Type of Internship", "")
    
    score = _get_deterministic_score(full_name, email, role)
    skills = _get_deterministic_skills(role)
    
    return {
        "id":          str(row_idx),
        "row":         row_idx,
        "name":        full_name,
        "email":       email,
        "phone":       d.get("Phone") or d.get("Mobile") or d.get("Contact No. (Preferably WhatsApp)", ""),
        "college":     d.get("College") or d.get("University") or d.get("College/Institution", ""),
        "cgpa":        d.get("CGPA") or d.get("GPA", ""),
        "role":        role,
        "status":      _normalize_status(d.get("Status", "")),
        "resumeScore": score,
        "skills":      skills,
        "appliedDate": d.get("Timestamp") or d.get("Date", ""),
        "resumeLink":  d.get("Resume Link") or d.get("Resume", ""),
        "_raw_status": d.get("Status", ""),
    }

STATUS_MAP = {
    "":                          "applied",
    "resume shortlisted":        "shortlisted",
    "not shortlisted":           "rejected",
    "invited for interview":     "interview",
    "interview accepted":        "accepted",
    "interview declined":        "rejected",
    "hired":                     "hired",
    "offer letter generated":    "offer",
    "internship ongoing":        "ongoing",
    "certificate generated":     "completed",
    "internship completed":      "completed",
    "rejected":                  "rejected",
}

def _normalize_status(raw: str) -> str:
    return STATUS_MAP.get(raw.strip().lower(), "applied")

class CandidateCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""
    college: Optional[str] = ""
    role: Optional[str] = ""
    cgpa: Optional[str] = ""
    resume_link: Optional[str] = ""
    skills: Optional[List[str]] = []

@app.post("/api/candidates")
def create_candidate(body: CandidateCreate):
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    if not url:
        raise HTTPException(400, "Registration sheet URL is not configured.")
    try:
        ws = open_sheet(url)
        all_values = get_sheet_values(url)
        headers = [h.strip() for h in all_values[0]] if all_values else [h.strip() for h in ws.row_values(1)]
        
        data = body.dict()
        row_values = []
        for h in headers:
            h_lower = h.lower()
            if "timestamp" in h_lower or ("date" in h_lower and "start" not in h_lower and "end" not in h_lower):
                row_values.append(datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
            elif "email" in h_lower:
                row_values.append(data.get("email") or "")
            elif "name" in h_lower:
                row_values.append(data.get("name") or "")
            elif "contact" in h_lower or "phone" in h_lower or "mobile" in h_lower:
                row_values.append(data.get("phone") or "")
            elif "college" in h_lower or "university" in h_lower or "institution" in h_lower:
                row_values.append(data.get("college") or "")
            elif "role" in h_lower or "position" in h_lower or "domain" in h_lower or "type of internship" in h_lower:
                row_values.append(data.get("role") or "")
            elif "resume" in h_lower:
                row_values.append(data.get("resume_link") or "")
            elif "cgpa" in h_lower or "gpa" in h_lower:
                row_values.append(data.get("cgpa") or "")
            elif "status" in h_lower:
                row_values.append("")  # Default status (blank/applied)
            else:
                row_values.append("")
        
        res = ws.append_row(row_values, value_input_option="USER_ENTERED")
        clear_data_cache()
        
        updated_range = res.get("updates", {}).get("updatedRange", "")
        match = re.search(r"(\d+)", updated_range.split("!")[-1])
        if match:
            new_row_idx = int(match.group(1))
        else:
            new_row_idx = len(ws.get_all_values())
            
        log_activity("shortlist", f"Added candidate {body.name} manually")
        return _row_to_candidate(headers, row_values, new_row_idx)
    except Exception as e:
        logger.error(f"create_candidate error: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/candidates")
def get_candidates(status: Optional[str] = None, search: Optional[str] = None):
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    if not url:
        return []
    try:
        all_values = get_sheet_values(url)
        if not all_values:
            return []
        headers = [h.strip() for h in all_values[0]]
        candidates = [_row_to_candidate(headers, row, i+2) for i, row in enumerate(all_values[1:])]
        if status and status != "all":
            candidates = [c for c in candidates if c["status"] == status]
        if search:
            q = search.lower()
            candidates = [c for c in candidates if
                q in c["name"].lower() or q in c["email"].lower() or q in c["college"].lower()]
        return candidates
    except Exception as e:
        logger.error(f"get_candidates error: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/candidates/{row_id}")
def get_candidate(row_id: int):
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    try:
        all_values = get_sheet_values(url)
        if not all_values or row_id - 1 >= len(all_values):
            raise HTTPException(404, "Candidate not found")
        headers = [h.strip() for h in all_values[0]]
        row = all_values[row_id - 1]
        return _row_to_candidate(headers, row, row_id)
    except Exception as e:
        raise HTTPException(404, str(e))

@app.put("/api/candidates/{row_id}/status")
def update_candidate_status(row_id: int, body: StatusUpdate):
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    try:
        all_values = get_sheet_values(url)
        headers = [h.strip() for h in all_values[0]] if all_values else []
        col = find_col(headers, "status")
        ws = open_sheet(url)
        if not col:
            headers = ws.row_values(1)
            col = find_col(headers, "status")
        if not col:
            raise HTTPException(400, "Status column not found in sheet")
        ws.update_cell(row_id, col, body.status)
        clear_data_cache()
        log_activity("hired" if "hired" in body.status.lower() else "shortlist", f"Status updated to '{body.status}'")
        return {"success": True, "new_status": body.status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

class BulkShortlistRequest(BaseModel):
    threshold: Optional[int] = None
    row_ids: Optional[List[int]] = None

@app.post("/api/candidates/bulk-shortlist")
def bulk_shortlist_candidates(body: BulkShortlistRequest):
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    if not url:
        raise HTTPException(400, "Registration sheet URL is not configured.")
    try:
        ws = open_sheet(url)
        all_values = get_sheet_values(url)
        if not all_values:
            return {"success": True, "count": 0}
        headers = [h.strip() for h in all_values[0]]
        status_col = find_col(headers, "status")
        if not status_col:
            raise HTTPException(400, "Status column not found in sheet")
            
        rows_to_update = []
        if body.row_ids:
            rows_to_update = body.row_ids
        elif body.threshold is not None:
            for i, row in enumerate(all_values[1:], 2):
                padded = row + [""] * (len(headers) - len(row))
                d = dict(zip(headers, padded))
                status = _normalize_status(d.get("Status", ""))
                if status != "applied":
                    continue
                f_name = d.get("Name") or d.get("Full Name") or d.get("First Name") or ""
                l_name = d.get("Last Name") or ""
                full_name = f"{f_name} {l_name}".strip() if f_name and l_name else f_name
                email = d.get("Email address") or d.get("Email") or ""
                role = d.get("Role") or d.get("Position") or d.get("Domain") or d.get("Type of Internship") or ""
                
                score = _get_deterministic_score(full_name, email, role)
                if score >= body.threshold:
                    rows_to_update.append(i)
                    
        if not rows_to_update:
            return {"success": True, "count": 0}
            
        cells = []
        for r_id in rows_to_update:
            cells.append(gspread.Cell(row=r_id, col=status_col, value="Resume Shortlisted"))
            
        ws.update_cells(cells, value_input_option="USER_ENTERED")
        clear_data_cache()
        log_activity("shortlist", f"Bulk shortlisted {len(rows_to_update)} candidates")
        return {"success": True, "count": len(rows_to_update)}
    except Exception as e:
        logger.error(f"bulk_shortlist_candidates error: {e}")
        raise HTTPException(500, str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/candidates/{row_id}/shortlist")
def shortlist_candidate(row_id: int):
    return update_candidate_status(row_id, StatusUpdate(status="Resume Shortlisted"))

@app.post("/api/candidates/{row_id}/reject")
def reject_candidate(row_id: int):
    return update_candidate_status(row_id, StatusUpdate(status="Rejected"))

@app.post("/api/candidates/{row_id}/hire")
def hire_candidate(row_id: int):
    return update_candidate_status(row_id, StatusUpdate(status="Hired"))

# ─── Interviews endpoints ─────────────────────────────────────────────────────
class BulkInviteRequest(BaseModel):
    row_ids: List[int]

@app.post("/api/interviews/send-invite/bulk")
def send_interview_invites_bulk(body: BulkInviteRequest, background_tasks: BackgroundTasks):
    load_dotenv(ENV_FILE, override=True)
    from send_invites import InterviewInviter
    
    inviter = InterviewInviter()
    if not inviter.connect():
        raise HTTPException(500, "Failed to connect to Google Sheets")
        
    errors = []
    try:
        all_values = get_sheet_values(inviter.sheet_url)
        headers = [h.strip() for h in all_values[0]] if all_values else []
    except Exception as e:
        logger.error(f"Failed to fetch values: {e}")
        raise HTTPException(500, f"Failed to read sheet: {e}")
        
    candidates_to_send = []
    for r_id in body.row_ids:
        try:
            if r_id - 1 >= len(all_values):
                continue
            row = all_values[r_id - 1]
            padded = row + [""] * (len(headers) - len(row))
            candidate = dict(zip(headers, padded))
            candidate['_row'] = r_id
            
            email = candidate.get("Email address") or candidate.get("Email")
            if email:
                candidates_to_send.append(candidate)
        except Exception as e:
            errors.append(f"Row {r_id}: {str(e)}")
            
    if not candidates_to_send:
        return {"success": True, "count": 0, "errors": errors}
        
    try:
        inviter.send_bulk_emails(candidates_to_send)
        clear_data_cache()
        names = [c.get("Name") or c.get("First Name") or "Candidate" for c in candidates_to_send]
        log_activity("interview", f"Bulk interview invites sent to {len(candidates_to_send)} candidates: {', '.join(names[:3])}")
        return {"success": True, "count": len(candidates_to_send), "errors": errors}
    except Exception as e:
        logger.error(f"bulk send_bulk_emails error: {e}")
        raise HTTPException(500, str(e))

@app.post("/api/interviews/send-invite/{row_id}")
def send_interview_invite(row_id: int, background_tasks: BackgroundTasks):
    load_dotenv(ENV_FILE, override=True)
    from send_invites import InterviewInviter
    inviter = InterviewInviter()
    if not inviter.connect():
        raise HTTPException(500, "Failed to connect to Google Sheets")
    try:
        row = inviter.worksheet.row_values(row_id)
        headers = inviter.worksheet.row_values(1)
        padded = row + [""] * (len(headers) - len(row))
        candidate = dict(zip(headers, padded))
        candidate['_row'] = row_id

        name = candidate.get("Name") or candidate.get("First Name") or "Candidate"
        email = candidate.get("Email address") or candidate.get("Email")
        if not email:
            raise HTTPException(400, "No email found for this candidate")

        inviter.send_bulk_emails([candidate])
        clear_data_cache()
        log_activity("interview", f"Interview invite sent to {name} ({email})")
        return {"success": True, "message": f"Invite sent to {email}"}
    except Exception as e:
        logger.error(f"send_interview_invite error: {e}")
        raise HTTPException(500, str(e))

# ─── Offers endpoints ───────────────────────────────────────────────────────────
@app.post("/api/offers/generate/{row_id}")
def generate_offer(row_id: int):
    try:
        import pythoncom
        pythoncom.CoInitialize()
        from generate_offers import OfferLetterGenerator
        gen = OfferLetterGenerator()
        sheet = gen.connect_services()
        if not sheet:
            raise HTTPException(500, "Failed to connect to Google Sheets")
        
        row = sheet.row_values(row_id)
        headers = sheet.row_values(1)
        padded = row + [""] * (len(headers) - len(row))
        candidate = dict(zip(headers, padded))
        
        m_role = candidate.get("Role") or "Software Developer - Intern"
        m_start = candidate.get("Start_Date") or candidate.get("Joining Date") or datetime.now().strftime("%B %d, %Y")
        manual_data = {'date': datetime.now().strftime("%B %d, %Y"), 'place': 'Bengaluru', 'role': m_role, 'start_date': m_start}
        
        output_path, file_name = gen.generate_offer_pdf(candidate, manual_data, row_id)
        if output_path and file_name and output_path.endswith('.pdf'):
            gen.upload_to_drive(output_path, file_name)
            gen.update_sheet_status(row_id, "Offer Letter Generated")
            clear_data_cache()
            log_activity("offer", f"Offer PDF generated for {candidate.get('Name') or candidate.get('First Name')}")
            return {"success": True, "message": "Offer letter generated", "pdfUrl": f"/api/offers/{file_name}"}
        raise HTTPException(500, "Failed to generate PDF")
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/offers/send/{row_id}")
def send_offer(row_id: int):
    try:
        from send_offer_letters import OfferEmailSender
        sender = OfferEmailSender()
        if not sender.connect():
            raise HTTPException(500, "Failed to connect to Google Sheets")
        
        row = sender.worksheet.row_values(row_id)
        headers = sender.worksheet.row_values(1)
        padded = row + [""] * (len(headers) - len(row))
        candidate = dict(zip(headers, padded))
        candidate['_row'] = row_id
        
        m_role = candidate.get("Role") or "Software Developer - Intern"
        m_start = candidate.get("Start_Date") or candidate.get("Joining Date") or datetime.now().strftime("%B %d, %Y")
        
        if sender.send_offer_email(candidate, {'role': m_role, 'start_date': m_start}):
            status_col = find_col(headers, "status")
            if status_col:
                sender.worksheet.update_cell(row_id, status_col, "Internship Ongoing")
            clear_data_cache()
            log_activity("offer", f"Offer letter sent to {candidate.get('Email') or candidate.get('Email address')}")
            return {"success": True, "message": "Offer letter sent via email"}
        raise HTTPException(500, "Failed to send email")
    except Exception as e:
        raise HTTPException(500, str(e))

# ─── Certificates endpoints ───────────────────────────────────────────────────
@app.post("/api/certs/generate/{row_id}")
def generate_certificate(row_id: int):
    try:
        import pythoncom
        pythoncom.CoInitialize()
        from generate_certificates import CertificateGenerator
        gen = CertificateGenerator()
        if not gen.connect():
            raise HTTPException(500, "Failed to connect")
        
        row = gen.sheet_instance.row_values(row_id)
        headers = gen.sheet_instance.row_values(1)
        padded = row + [""] * (len(headers) - len(row))
        candidate = dict(zip(headers, padded))
        
        sheet_start = gen.get_val(candidate, ["Start_Date", "Start Date", "Joining Date"]) or datetime.now().strftime("%B %d, %Y")
        sheet_end = gen.get_val(candidate, ["End_Date", "End Date", "Completion Date"]) or datetime.now().strftime("%B %d, %Y")
        m_role = gen.get_val(candidate, ["Role"]) or "Software Developer - Intern"
        
        docx, pdf, certificate_id = gen.generate_docx(candidate, {'start': sheet_start, 'end': sheet_end}, {'issue_date': datetime.now().strftime("%B %d, %Y"), 'role': m_role})
        
        if docx and pdf and gen.convert_to_pdf(docx, pdf):
            if os.path.exists(pdf):
                gen.upload_to_drive(pdf, os.path.basename(pdf))
            gen.update_sheet_field(row_id, ["Certificate ID", "Certificate_ID", "CERTIFICATE_ID"], certificate_id)
            gen.update_status(row_id, "Certificate Generated")
            clear_data_cache()
            log_activity("certificate", f"Certificate generated for {candidate.get('Name') or candidate.get('First Name')}")
            return {"success": True, "message": "Certificate generated successfully", "pdfUrl": f"/api/certs/{os.path.basename(pdf)}"}
        raise HTTPException(500, "Failed to generate certificate PDF")
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/certs/send/{row_id}")
def send_cert(row_id: int):
    try:
        from send_completion import CompletionEmailSender
        sender = CompletionEmailSender()
        if not sender.connect():
            raise HTTPException(500, "Failed to connect")
        
        row = sender.sheet_instance.row_values(row_id)
        headers = sender.sheet_instance.row_values(1)
        padded = row + [""] * (len(headers) - len(row))
        candidate = dict(zip(headers, padded))
        candidate['_row'] = row_id
        
        m_role = candidate.get("Role") or "Software Developer - Intern"
        sheet_start = candidate.get("Start_Date") or datetime.now().strftime("%B %d, %Y")
        sheet_end = candidate.get("End_Date") or datetime.now().strftime("%B %d, %Y")
        
        opt9_candidate = {
            'Name': candidate.get("Name") or candidate.get("First Name") or "Candidate",
            'Email': candidate.get("Email address") or candidate.get("Email") or ""
        }
        if sender.send_email(opt9_candidate):
            status_col = find_col(headers, "status")
            if status_col:
                sender.sheet_instance.update_cell(row_id, status_col, "Internship Completed")
            clear_data_cache()
            log_activity("certificate", f"Completion email sent to {candidate.get('Email') or candidate.get('Email address')}")
            return {"success": True, "message": "Completion email sent"}
        raise HTTPException(500, "Failed to send email")
    except Exception as e:
        raise HTTPException(500, str(e))

def convert_docx_to_pdf_win32(docx_path: Path, pdf_path: Path) -> bool:
    try:
        import win32com.client
        import pythoncom
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(str(docx_path))
        doc.SaveAs(str(pdf_path), FileFormat=17)
        doc.Close()
        word.Quit()
        return True
    except Exception as e:
        logger.error(f"win32com PDF conversion failed: {e}")
        return False

def _get_candidate_pdf_info(row_id: int):
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    ws = open_sheet(url)
    row = ws.row_values(row_id)
    headers = ws.row_values(1)
    padded = row + [""] * (len(headers) - len(row))
    c = dict(zip(headers, padded))
    
    f_name = c.get("First Name") or c.get("Name") or "Candidate"
    l_name = c.get("Last Name")
    full_name = f"{f_name} {l_name}".strip() if f_name and l_name else f_name
    email = (c.get("Email address") or c.get("Email") or "no_email").strip()
    
    safe_name = "".join([ch if ch.isalnum() or ch == '_' else "_" for ch in full_name])
    email_prefix = email.split('@')[0] if email else "no_email"
    return safe_name, email_prefix, email, full_name

@app.post("/api/candidates/{row_id}/upload-offer")
async def upload_offer_letter(row_id: int, file: UploadFile = File(...)):
    try:
        safe_name, email_prefix, email, full_name = _get_candidate_pdf_info(row_id)
        output_dir = BASE_DIR / "scripts" / "output" / "offer_letters"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        ext = Path(file.filename).suffix.lower()
        if ext not in [".pdf", ".docx"]:
            raise HTTPException(400, "Only PDF and DOCX files are allowed")
            
        temp_filename = f"Offer_{safe_name}_{email_prefix}{ext}"
        temp_path = output_dir / temp_filename
        
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
            
        pdf_filename = f"Offer_{safe_name}_{email_prefix}.pdf"
        pdf_path = output_dir / pdf_filename
        
        if ext == ".docx":
            success = convert_docx_to_pdf_win32(temp_path, pdf_path)
            if success and temp_path.exists():
                temp_path.unlink()
            elif not success:
                raise HTTPException(500, "Failed to convert DOCX to PDF. Make sure Microsoft Word is installed.")
                
        url = os.getenv("REGISTRATION_SHEET_URL", "")
        ws = open_sheet(url)
        headers = ws.row_values(1)
        status_col = find_col(headers, "status")
        if status_col:
            ws.update_cell(row_id, status_col, "Offer Letter Generated")
            clear_data_cache()
            
        log_activity("offer", f"Uploaded offer letter for {full_name}")
        return {"success": True, "message": "Offer letter uploaded successfully", "pdfUrl": f"/api/offers/{pdf_filename}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"upload_offer_letter error: {e}")
        raise HTTPException(500, str(e))

@app.post("/api/candidates/{row_id}/upload-cert")
async def upload_certificate(row_id: int, file: UploadFile = File(...)):
    try:
        safe_name, email_prefix, email, full_name = _get_candidate_pdf_info(row_id)
        output_dir = BASE_DIR / "scripts" / "output" / "certificates"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        ext = Path(file.filename).suffix.lower()
        if ext not in [".pdf", ".docx"]:
            raise HTTPException(400, "Only PDF and DOCX files are allowed")
            
        temp_filename = f"Cert_{safe_name}_{email_prefix}{ext}"
        temp_path = output_dir / temp_filename
        
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
            
        pdf_filename = f"Cert_{safe_name}_{email_prefix}.pdf"
        pdf_path = output_dir / pdf_filename
        
        if ext == ".docx":
            success = convert_docx_to_pdf_win32(temp_path, pdf_path)
            if success and temp_path.exists():
                temp_path.unlink()
            elif not success:
                raise HTTPException(500, "Failed to convert DOCX to PDF. Make sure Microsoft Word is installed.")
                
        url = os.getenv("REGISTRATION_SHEET_URL", "")
        ws = open_sheet(url)
        headers = ws.row_values(1)
        status_col = find_col(headers, "status")
        if status_col:
            ws.update_cell(row_id, status_col, "Certificate Generated")
            clear_data_cache()
            
        log_activity("certificate", f"Uploaded certificate for {full_name}")
        return {"success": True, "message": "Certificate uploaded successfully", "pdfUrl": f"/api/certs/{pdf_filename}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"upload_certificate error: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/offers/{filename}")
def get_offer_pdf(filename: str):
    path = BASE_DIR / "scripts" / "output" / "offer_letters" / filename
    if not path.exists():
        raise HTTPException(404, "Offer letter not found")
    return FileResponse(path, media_type="application/pdf", filename=filename)

@app.get("/api/certs/{filename}")
def get_cert_pdf(filename: str):
    path = BASE_DIR / "scripts" / "output" / "certificates" / filename
    if not path.exists():
        raise HTTPException(404, "Certificate not found")
    return FileResponse(path, media_type="application/pdf", filename=filename)

@app.get("/api/offers/preview/{row_id}")
def preview_offer_template(row_id: int):
    try:
        from send_offer_letters import OfferEmailSender
        sender = OfferEmailSender()
        if not sender.connect():
            raise HTTPException(500, "Failed to connect to Google Sheets")
            
        row = sender.worksheet.row_values(row_id)
        headers = sender.worksheet.row_values(1)
        padded = row + [""] * (len(headers) - len(row))
        candidate = dict(zip(headers, padded))
        
        m_role = candidate.get("Role") or "Software Developer - Intern"
        m_start = candidate.get("Start_Date") or candidate.get("Joining Date") or datetime.now().strftime("%B %d, %Y")
        
        # Format dates
        from datetime import datetime, timedelta
        try:
            parsed_start = datetime.strptime(m_start, "%d-%m-%Y")
        except:
            try:
                parsed_start = datetime.strptime(m_start, "%Y-%m-%d")
            except:
                parsed_start = datetime.now()
                
        expiry_date = parsed_start - timedelta(days=2)
        start_date_str = parsed_start.strftime("%B %d, %Y")
        expiry_date_str = expiry_date.strftime("%B %d, %Y")
        
        with open(sender.template_path, "r", encoding="utf-8") as f:
            tpl = f.read()
            
        signature = os.getenv("EMAIL_SIGNATURE", "Regards,\nHR Team\nSwipeGen Technologies").replace("\n", "<br>")
        full_name = candidate.get("Name") or candidate.get("First Name") or "Candidate"
        
        html_content = tpl.replace("{name}", full_name.split()[0])
        html_content = html_content.replace("{role}", m_role)
        html_content = html_content.replace("{start_date}", start_date_str)
        html_content = html_content.replace("{expiry_date}", expiry_date_str)
        html_content = html_content.replace("{signature}", signature)
        
        # Public CDN image replacements for live preview rendering
        html_content = html_content.replace("cid:logo_url", "https://www.swipegen.com/logo.png")
        html_content = html_content.replace("cid:ig_icon", "https://img.icons8.com/color/48/instagram-new--v1.png")
        html_content = html_content.replace("cid:li_icon", "https://img.icons8.com/color/48/linkedin.png")
        html_content = html_content.replace("cid:google_icon", "https://img.icons8.com/color/48/google-logo.png")
        
        for key, val in sender.social_links.items():
            if "cid:" not in str(val):
                html_content = html_content.replace(f"{{{key}}}", str(val))
                
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"preview_offer_template error: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/certs/preview/{row_id}")
def preview_cert_template(row_id: int):
    try:
        from send_completion import CompletionEmailSender
        sender = CompletionEmailSender()
        if not sender.connect():
            raise HTTPException(500, "Failed to connect to Google Sheets")
            
        row = sender.sheet_instance.row_values(row_id)
        headers = sender.sheet_instance.row_values(1)
        padded = row + [""] * (len(headers) - len(row))
        candidate = dict(zip(headers, padded))
        
        with open(sender.template_path, "r", encoding="utf-8") as f:
            tpl = f.read()
            
        signature = os.getenv("EMAIL_SIGNATURE", "Regards,\nHR Team\nSwipeGen Technologies").replace("\n", "<br>")
        full_name = candidate.get("Name") or candidate.get("First Name") or "Candidate"
        
        html_content = tpl.replace("{name}", full_name.split()[0])
        html_content = html_content.replace("{signature}", signature)
        
        html_content = html_content.replace("cid:logo_url", "https://www.swipegen.com/logo.png")
        html_content = html_content.replace("cid:ig_icon", "https://img.icons8.com/color/48/instagram-new--v1.png")
        html_content = html_content.replace("cid:li_icon", "https://img.icons8.com/color/48/linkedin.png")
        html_content = html_content.replace("cid:google_icon", "https://img.icons8.com/color/48/google-logo.png")
        
        for key, val in sender.social_links.items():
            if "cid:" not in str(val):
                html_content = html_content.replace(f"{{{key}}}", str(val))
                
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"preview_cert_template error: {e}")
        raise HTTPException(500, str(e))

# ─── Stats / Dashboard ────────────────────────────────────────────────────────
@app.get("/api/stats")
def get_stats():
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    if not url:
        return _empty_stats()
    try:
        all_values = get_sheet_values(url)
        records = get_sheet_records_from_values(all_values)
        counts = {s: 0 for s in STATUS_MAP.values()}
        for r in records:
            raw = str(r.get("Status", "")).strip()
            norm = _normalize_status(raw)
            counts[norm] = counts.get(norm, 0) + 1

        # Activity log
        activities = []
        if SENT_LOG.exists():
            try:
                activities = json.loads(SENT_LOG.read_text())[:5]
            except Exception:
                pass

        return {
            "totalCandidates":    len(records),
            "newApplications":    counts.get("applied", 0),
            "shortlisted":        counts.get("shortlisted", 0),
            "interviewScheduled": counts.get("interview", 0),
            "interviewAccepted":  counts.get("accepted", 0),
            "hired":              counts.get("hired", 0),
            "offerSent":          counts.get("offer", 0),
            "completed":          counts.get("completed", 0),
            "todayInterviews":    [],
            "recentActivities":   activities,
            "pendingActions":     _get_pending_actions(counts),
        }
    except Exception as e:
        logger.error(f"get_stats error: {e}")
        return _empty_stats()

def _empty_stats():
    return {
        "totalCandidates": 0, "newApplications": 0, "shortlisted": 0,
        "interviewScheduled": 0, "interviewAccepted": 0, "hired": 0,
        "offerSent": 0, "completed": 0,
        "todayInterviews": [], "recentActivities": [], "pendingActions": [],
    }

def _get_pending_actions(counts: dict) -> list:
    actions = []
    if counts.get("shortlisted", 0) > 0:
        actions.append({"id":1,"type":"interview","message":f"{counts['shortlisted']} shortlisted candidates awaiting interview invite","urgent":True})
    if counts.get("hired", 0) > 0:
        actions.append({"id":2,"type":"offer","message":f"{counts['hired']} hired candidates awaiting offer letter","urgent":True})
    if counts.get("offer", 0) > 0:
        actions.append({"id":3,"type":"cert","message":f"{counts['offer']} candidates awaiting certificate","urgent":False})
    return actions

# ─── Activity Log ─────────────────────────────────────────────────────────────
@app.get("/api/activities")
def get_activities():
    if SENT_LOG.exists():
        try:
            return json.loads(SENT_LOG.read_text())
        except Exception:
            pass
    return []

# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    load_dotenv(ENV_FILE, override=True)
    return {
        "status": "ok",
        "sheet_configured": bool(os.getenv("REGISTRATION_SHEET_URL")),
        "smtp_configured":  bool(os.getenv("SENDER_EMAIL") and os.getenv("SENDER_PASSWORD")),
        "sa_file_exists":   SA_FILE.exists(),
    }
