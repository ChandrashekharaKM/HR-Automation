"""
utils/resume_analyser.py
------------------------
AI-powered resume analysis using Google Gemini.

Given a Google Drive resume link, this module:
  1. Downloads the file (PDF/DOCX) via Google Drive API using the service account.
  2. Sends the raw text / binary content to Gemini 1.5 Flash.
  3. Returns a structured analysis report containing:
       - AI-generated content % estimate
       - Extracted skills
       - Experience summary
       - Education
       - Red flags
       - Overall suitability score (0-10)

Dependencies:
  pip install google-generativeai
"""

import os
import re
import io
import logging
import tempfile
import urllib.parse

import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# ANSI Colour Codes
# ──────────────────────────────────────────────────────────────────
G, R, Y, B, C, M, W = (
    '\033[92m', '\033[91m', '\033[93m',
    '\033[94m', '\033[96m', '\033[95m', '\033[0m'
)


# ──────────────────────────────────────────────────────────────────
# DRIVE HELPER  — download a file given its public/share URL
# ──────────────────────────────────────────────────────────────────

def _extract_drive_file_id(url: str) -> str | None:
    """
    Extract a Google Drive file ID from any of the common URL formats:
      - https://drive.google.com/file/d/<ID>/view
      - https://drive.google.com/open?id=<ID>
      - https://docs.google.com/...?id=<ID>
    """
    # Pattern 1: /file/d/<ID>/
    m = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if m:
        return m.group(1)
    # Pattern 2: ?id=<ID>  or  &id=<ID>
    m = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if m:
        return m.group(1)
    return None


def _download_drive_file(file_id: str, creds_file: str) -> tuple[bytes, str]:
    """
    Download a file from Google Drive using the service account.

    Returns:
        (raw_bytes, mime_type)
    """
    creds = service_account.Credentials.from_service_account_file(
        creds_file,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    drive = build('drive', 'v3', credentials=creds)

    # Get file metadata first (to know the mime type)
    meta = drive.files().get(fileId=file_id, fields='name,mimeType').execute()
    mime_type = meta.get('mimeType', 'application/octet-stream')
    logger.info(f"Downloading Drive file: {meta.get('name')} ({mime_type})")

    # For Google Docs/Slides/Sheets → export as PDF
    google_doc_mimes = {
        'application/vnd.google-apps.document':     'application/pdf',
        'application/vnd.google-apps.presentation': 'application/pdf',
        'application/vnd.google-apps.spreadsheet':  'text/csv',
    }

    buf = io.BytesIO()
    if mime_type in google_doc_mimes:
        export_mime = google_doc_mimes[mime_type]
        request = drive.files().export_media(fileId=file_id, mimeType=export_mime)
        mime_type = export_mime
    else:
        request = drive.files().get_media(fileId=file_id)

    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    return buf.getvalue(), mime_type


# ──────────────────────────────────────────────────────────────────
# GEMINI ANALYSER
# ──────────────────────────────────────────────────────────────────

_ANALYSIS_PROMPT = """
You are an expert HR recruiter and resume analyst. Carefully analyse this resume and return a structured JSON report.

Respond with ONLY valid JSON (no markdown, no extra text), in this exact format:
{{
  "candidate_name": "Full Name if found, else Unknown",
  "ai_content_percent": <integer 0-100>,
  "ai_content_verdict": "<Low | Medium | High>",
  "suitability_score": <integer 0-10>,
  "suitability_verdict": "<Poor | Below Average | Average | Good | Excellent>",
  "skills": ["skill1", "skill2", ...],
  "experience_years": <number or null if unknown>,
  "experience_summary": "1-2 sentence summary of work experience",
  "education": "Highest degree and institution",
  "certifications": ["cert1", "cert2"],
  "red_flags": ["flag1", "flag2"],
  "strengths": ["strength1", "strength2"],
  "role_fit_reasoning": "1-2 sentences explaining why this candidate is or is not a good fit for a software internship"
}}

Rules:
- ai_content_percent: Estimate how much of the resume text appears AI-generated (repetitive phrasing, buzzword stuffing, generic descriptions). 0 = fully human-written. 100 = clearly AI-generated.
- suitability_score: 0 = completely unsuitable, 10 = perfect candidate.
- red_flags: List genuine concerns (job hopping, exaggerated claims, gaps, inconsistencies).
- Be factual and concise. No filler words.
"""


def analyse_resume(
    resume_url: str,
    creds_file: str,
    api_key: str,
    role: str = "Software Developer - Intern"
) -> dict | None:
    """
    Download a resume from Google Drive and analyse it with Gemini.

    Args:
        resume_url:  Google Drive share URL from the candidate sheet.
        creds_file:  Path to service_account.json.
        api_key:     Gemini API key (from GEMINI_API_KEY env var).
        role:        Target role for fit assessment.

    Returns:
        dict with analysis results, or None on failure.
    """
    # ── 1. Extract file ID ──────────────────────────────────────
    file_id = _extract_drive_file_id(resume_url)
    if not file_id:
        logger.warning(f"Could not extract Drive file ID from URL: {resume_url}")
        return None

    # ── 2. Download file ────────────────────────────────────────
    try:
        raw_bytes, mime_type = _download_drive_file(file_id, creds_file)
    except Exception as e:
        logger.error(f"Failed to download resume (file_id={file_id}): {e}")
        return None

    # ── 3. Configure Gemini ─────────────────────────────────────
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # ── 4. Upload file to Gemini Files API ──────────────────────
    # Save to a temp file so Gemini can process it
    try:
        suffix = '.pdf' if 'pdf' in mime_type else '.docx'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(raw_bytes)
            tmp_path = tmp.name

        uploaded = genai.upload_file(tmp_path, mime_type=mime_type)
        prompt = _ANALYSIS_PROMPT.replace('{{', '{').replace('}}', '}').format()  # clean braces

        response = model.generate_content([
            uploaded,
            f"The target role is: {role}\n\n{_ANALYSIS_PROMPT}"
        ])
        os.unlink(tmp_path)  # cleanup temp file
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return None

    # ── 5. Parse JSON response ──────────────────────────────────
    import json
    raw_text = response.text.strip()

    # Strip markdown code fences if Gemini wraps in ```json ... ```
    raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
    raw_text = re.sub(r'\s*```$', '', raw_text)

    try:
        result = json.loads(raw_text)
        logger.info(f"Resume analysed successfully. Score: {result.get('suitability_score')}/10")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON response: {e}\nRaw: {raw_text[:300]}")
        return None


# ──────────────────────────────────────────────────────────────────
# DISPLAY HELPER — pretty-print the analysis report
# ──────────────────────────────────────────────────────────────────

def print_analysis_report(report: dict):
    """Render the AI analysis report in a rich, coloured CLI format."""

    score = report.get('suitability_score', 0)
    ai_pct = report.get('ai_content_percent', 0)
    ai_verdict = report.get('ai_content_verdict', '')

    # Score colour
    score_colour = G if score >= 7 else (Y if score >= 4 else R)

    # AI content colour (red if high AI, green if low)
    ai_colour = R if ai_pct >= 60 else (Y if ai_pct >= 30 else G)

    # Build visual score bar
    filled = int(score)
    score_bar = f"{'█' * filled}{'░' * (10 - filled)}"

    # Build AI% bar
    ai_filled = int(ai_pct / 10)
    ai_bar = f"{'█' * ai_filled}{'░' * (10 - ai_filled)}"

    print(f"\n{M}{'━'*70}")
    print(f"  🤖  AI RESUME ANALYSIS REPORT")
    print(f"{'━'*70}{W}")

    # ── Suitability Score ──
    print(f"\n  {B}📊 SUITABILITY SCORE{W}")
    print(f"     {score_colour}{score_bar}  {score}/10  ({report.get('suitability_verdict', '')}){W}")

    # ── AI Content ──
    print(f"\n  {B}🧠 AI-GENERATED CONTENT{W}")
    print(f"     {ai_colour}{ai_bar}  {ai_pct}%  ({ai_verdict}){W}")
    if ai_pct >= 60:
        print(f"     {R}⚠️  Resume appears heavily AI-written — verify authenticity!{W}")
    elif ai_pct >= 30:
        print(f"     {Y}⚠️  Some AI-assisted sections detected.{W}")
    else:
        print(f"     {G}✅ Resume appears mostly human-written.{W}")

    # ── Skills ──
    skills = report.get('skills', [])
    print(f"\n  {B}🛠️  SKILLS  ({len(skills)} detected){W}")
    if skills:
        # Print in rows of 4
        for i in range(0, len(skills), 4):
            row = skills[i:i+4]
            print("     " + "   ".join(f"{C}• {s}{W}" for s in row))
    else:
        print(f"     {Y}No skills detected.{W}")

    # ── Experience ──
    exp_yrs = report.get('experience_years')
    exp_summary = report.get('experience_summary', 'N/A')
    print(f"\n  {B}💼 EXPERIENCE{W}")
    if exp_yrs is not None:
        print(f"     Years: {Y}{exp_yrs}{W}")
    print(f"     {exp_summary}")

    # ── Education ──
    edu = report.get('education', 'N/A')
    print(f"\n  {B}🎓 EDUCATION{W}")
    print(f"     {edu}")

    # ── Certifications ──
    certs = report.get('certifications', [])
    if certs:
        print(f"\n  {B}📜 CERTIFICATIONS{W}")
        for cert in certs:
            print(f"     {G}✓ {cert}{W}")

    # ── Strengths ──
    strengths = report.get('strengths', [])
    if strengths:
        print(f"\n  {B}💪 STRENGTHS{W}")
        for s in strengths:
            print(f"     {G}+ {s}{W}")

    # ── Red Flags ──
    flags = report.get('red_flags', [])
    if flags:
        print(f"\n  {B}🚩 RED FLAGS{W}")
        for f in flags:
            print(f"     {R}⚠ {f}{W}")
    else:
        print(f"\n  {G}✅ No red flags detected.{W}")

    # ── Role Fit ──
    fit = report.get('role_fit_reasoning', '')
    if fit:
        print(f"\n  {B}🎯 ROLE FIT ASSESSMENT{W}")
        print(f"     {fit}")

    print(f"\n{M}{'━'*70}{W}\n")
