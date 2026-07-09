"""
HR Admin Portal — FastAPI Backend
==================================
Bridges the React frontend to the existing Python automation scripts.
Each endpoint calls the corresponding script logic directly.

Run with:
    pip install fastapi uvicorn python-dotenv gspread oauth2client
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

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
from fastapi import FastAPI, HTTPException, BackgroundTasks
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

def get_client() -> gspread.Client:
    if not SA_FILE.exists():
        raise HTTPException(500, "service_account.json not found in scripts/")
    creds = ServiceAccountCredentials.from_json_keyfile_name(str(SA_FILE), SCOPE)
    return gspread.authorize(creds)

def open_sheet(url: str) -> gspread.Worksheet:
    if not url:
        raise HTTPException(400, "Sheet URL is not configured. Set it in Settings.")
    client = get_client()
    spreadsheet = client.open_by_url(url)
    gid_match = re.search(r"gid=([0-9]+)", url)
    if gid_match:
        target_gid = int(gid_match.group(1))
        for ws in spreadsheet.worksheets():
            if ws.id == target_gid:
                return ws
    return spreadsheet.get_worksheet(0)

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

# ─── Candidates endpoints ─────────────────────────────────────────────────────
def _row_to_candidate(headers: list, row: list, row_idx: int) -> dict:
    padded = row + [""] * (len(headers) - len(row))
    d = dict(zip(headers, padded))
    return {
        "id":          str(row_idx),
        "row":         row_idx,
        "name":        d.get("Name") or d.get("Full Name") or d.get("First Name", ""),
        "email":       d.get("Email address") or d.get("Email", ""),
        "phone":       d.get("Phone") or d.get("Mobile", ""),
        "college":     d.get("College") or d.get("University", ""),
        "cgpa":        d.get("CGPA") or d.get("GPA", ""),
        "role":        d.get("Role") or d.get("Position") or d.get("Domain", ""),
        "status":      _normalize_status(d.get("Status", "")),
        "resumeScore": 0,
        "skills":      [],
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
    "internship ongoing":        "hired",
    "certificate generated":     "completed",
    "internship completed":      "completed",
    "rejected":                  "rejected",
}

def _normalize_status(raw: str) -> str:
    return STATUS_MAP.get(raw.strip().lower(), "applied")

@app.get("/api/candidates")
def get_candidates(status: Optional[str] = None, search: Optional[str] = None):
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    if not url:
        return []
    try:
        ws = open_sheet(url)
        all_values = ws.get_all_values()
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
        ws   = open_sheet(url)
        headers = [h.strip() for h in ws.row_values(1)]
        row  = ws.row_values(row_id)
        return _row_to_candidate(headers, row, row_id)
    except Exception as e:
        raise HTTPException(404, str(e))

@app.put("/api/candidates/{row_id}/status")
def update_candidate_status(row_id: int, body: StatusUpdate):
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    try:
        ws = open_sheet(url)
        headers = ws.row_values(1)
        col = find_col(headers, "status")
        if not col:
            raise HTTPException(400, "Status column not found in sheet")
        ws.update_cell(row_id, col, body.status)
        log_activity("hired" if "hired" in body.status.lower() else "shortlist", f"Status updated to '{body.status}'")
        return {"success": True, "new_status": body.status}
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
@app.post("/api/interviews/send-invite/{row_id}")
def send_interview_invite(row_id: int, background_tasks: BackgroundTasks):
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    sender = os.getenv("SENDER_EMAIL", "")
    pwd    = os.getenv("SENDER_PASSWORD", "")
    port   = int(os.getenv("SMTP_PORT", "587"))

    if not sender or not pwd:
        raise HTTPException(400, "SMTP credentials not configured. Set them in Settings.")

    try:
        ws = open_sheet(url)
        headers = ws.row_values(1)
        row     = ws.row_values(row_id)
        padded  = row + [""] * (len(headers) - len(row))
        d       = dict(zip(headers, padded))
        name    = d.get("Name") or d.get("First Name", "Candidate")
        email   = d.get("Email address") or d.get("Email", "")

        if not email:
            raise HTTPException(400, "No email found for this candidate")

        # Send email
        msg = f"Subject: Interview Invitation - HR Portal\n\nDear {name},\n\nYou have been shortlisted for an interview. Please confirm your availability.\n\nBest regards,\nHR Team"
        with smtplib.SMTP("smtp.gmail.com", port) as server:
            server.starttls()
            server.login(sender, pwd)
            server.sendmail(sender, email, msg)

        # Update status
        col = find_col(headers, "status")
        if col:
            ws.update_cell(row_id, col, "Invited for Interview")

        log_activity("interview", f"Interview invite sent to {name} ({email})")
        return {"success": True, "message": f"Invite sent to {email}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

# ─── Offers endpoints ───────────────────────────────────────────────────────────
@app.post("/api/offers/generate/{row_id}")
def generate_offer(row_id: int):
    try:
        from option6_generate_offers import OfferLetterGenerator
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
            log_activity("offer", f"Offer PDF generated for {candidate.get('Name') or candidate.get('First Name')}")
            return {"success": True, "message": "Offer letter generated", "pdfUrl": f"/api/offers/{file_name}"}
        raise HTTPException(500, "Failed to generate PDF")
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/offers/send/{row_id}")
def send_offer(row_id: int):
    try:
        from option7_send_offer_letters import OfferEmailSender
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
            log_activity("offer", f"Offer letter sent to {candidate.get('Email') or candidate.get('Email address')}")
            return {"success": True, "message": "Offer letter sent via email"}
        raise HTTPException(500, "Failed to send email")
    except Exception as e:
        raise HTTPException(500, str(e))

# ─── Certificates endpoints ───────────────────────────────────────────────────
@app.post("/api/certs/generate/{row_id}")
def generate_cert(row_id: int):
    try:
        from option8_generate_certificates import CertificateGenerator
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
            log_activity("certificate", f"Certificate generated for {candidate.get('Name') or candidate.get('First Name')}")
            return {"success": True, "message": "Certificate generated successfully", "pdfUrl": f"/api/certs/{os.path.basename(pdf)}"}
        raise HTTPException(500, "Failed to generate certificate PDF")
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/certs/send/{row_id}")
def send_cert(row_id: int):
    try:
        from option9_send_completion import CompletionEmailSender
        sender = CompletionEmailSender()
        if not sender.connect():
            raise HTTPException(500, "Failed to connect")
        
        row = sender.worksheet.row_values(row_id)
        headers = sender.worksheet.row_values(1)
        padded = row + [""] * (len(headers) - len(row))
        candidate = dict(zip(headers, padded))
        candidate['_row'] = row_id
        
        m_role = candidate.get("Role") or "Software Developer - Intern"
        sheet_start = candidate.get("Start_Date") or datetime.now().strftime("%B %d, %Y")
        sheet_end = candidate.get("End_Date") or datetime.now().strftime("%B %d, %Y")
        
        if sender.send_completion_email(candidate, {'role': m_role, 'start_date': sheet_start, 'end_date': sheet_end}):
            status_col = find_col(headers, "status")
            if status_col:
                sender.worksheet.update_cell(row_id, status_col, "Internship Completed")
            log_activity("certificate", f"Completion email sent to {candidate.get('Email') or candidate.get('Email address')}")
            return {"success": True, "message": "Completion email sent"}
        raise HTTPException(500, "Failed to send email")
    except Exception as e:
        raise HTTPException(500, str(e))

# ─── Stats / Dashboard ────────────────────────────────────────────────────────
@app.get("/api/stats")
def get_stats():
    load_dotenv(ENV_FILE, override=True)
    url = os.getenv("REGISTRATION_SHEET_URL", "")
    if not url:
        return _empty_stats()
    try:
        ws = open_sheet(url)
        records = ws.get_all_records()
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
