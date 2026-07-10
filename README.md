# 🚀 SwipeGen-Automation

SwipeGen-Automation is an automation toolkit designed to streamline recruitment workflows — from candidate shortlisting to offer letters and completion certificates.

## 📋 Overview

This repository contains Python scripts and a frontend app that automate critical HR processes including:

## 🔐 Ownership and Authority
All administrative authority and ownership of this project are assigned to the project owner. This workspace is managed by the owner for HR-Automation operations.
- Candidate shortlisting and registration management
- Interview invitation distribution
- Recruitment summary reporting
- Hiring status updates
- Offer letter generation and distribution
- Internship completion certificate generation
- Completion email notifications

## ✨ Features

### 1. 📝 Candidate Management
- View and shortlist candidate registrations
- Track candidate status throughout the workflow

### 2. 📧 Communication
- Send automated interview invites
- Distribute offer letters via email
- Send completion certificates and notifications
- Customizable email templates

### 3. 📊 Reporting
- Generate comprehensive recruitment summary reports
- Track hiring pipeline metrics
- Monitor internship completion status

### 4. 📄 Document Generation
- Auto-generate offer letters (PDF)
- Create internship completion certificates
- Template-based document customization

### 5. 🔄 Workflow Automation
- End-to-end automation from interview to completion
- Status tracking and updates
- History logging for all operations

## 📁 Project Structure

```
SwipeGen-Automation/
├── README.md                          # Project documentation
├── config.json                        # Configuration settings
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
├── frontend/                          # Web frontend (Vite + React / TS)
│  ├── package.json
│  └── src/
├── scripts/
│   ├── main_menu.py                  # Main application menu
│   ├── option1_view_shortlist.py     # View & shortlist candidates
│   ├── option2_send_invites.py       # Send interview invites
│   ├── option3_generate_summary.py   # Generate reports
│   ├── option4_update_hired.py       # Update hired status
│   ├── option5_send_details_req.py   # Request offer details
│   ├── option6_generate_offers.py    # Generate offer letters
│   ├── option7_send_offer_letters.py # Send offer letters
│   ├── option8_generate_certificates.py # Generate certificates
│   ├── option9_send_completion.py    # Send completion emails
│   ├── credentials.json              # Google API credentials (not tracked)
│   ├── service_account.json          # Service account file (not tracked)
│   ├── sent_history.json             # History of sent communications
│   └── __pycache__/                  # Python cache (not tracked)
│
├── templates/
│   ├── interview_template.txt        # Interview invitation template
│   ├── offer_email_template.html     # Offer letter email template
│   ├── offer_details_template.txt    # Offer details request template
│   └── completion_email_template.html # Completion notification template
│
└── output/
   ├── certificates/                 # Generated certificates
   └── offer_letters/                # Generated offer letters
```

## 🏗️ Architecture

This project follows a simple, modular architecture designed for flexibility and automation across frontend, backend, and cloud integrations.

- **Frontend (UI)**: The user-facing app lives in [frontend/](frontend/) and is built with Vite + React (some TypeScript). It provides dashboards, candidate views, and calls the backend APIs or scripts for actions.
- **Backend (Automation Scripts)**: Core automation lives in [scripts/](scripts/) as a set of Python CLI scripts that implement the workflow (shortlisting, invites, offer generation, certificate generation, email sending). Use `scripts/main_menu.py` to run the CLI.
- **API Layer**: A minimal programmatic API entrypoint is available at [api.py](api.py) (FastAPI) to expose selected automation features for integration or for the frontend to consume.
- **Data & Storage**: Google Sheets stores registration, interview responses, and offer details (configured via environment variables in [scripts/.env](scripts/.env)). Generated documents are stored in `output/` and optionally uploaded to Google Drive folders (Drive IDs configured in `.env`).
- **Email & Templates**: SMTP is used for sending emails (credentials in [scripts/.env](scripts/.env)). Email and document templates are in [templates/](templates/) and are applied to generate offer letters and completion certificates.
- **Flow Overview**: Registration → Shortlisting → Interview Invites → Update Status → Request Offer Details → Generate Offer Letters → Send Offers → Generate Certificates → Send Completion Emails → Reporting.

This design separates concerns: lightweight frontend for UX, a collection of tested scripts for automation tasks, and an optional API for integrations.

## 🚀 Getting Started

### Architecture Diagram

```mermaid
flowchart LR
   subgraph UI[Frontend]
      FE[Vite + React]
   end

   subgraph API[Programmatic API]
      APINode[FastAPI - api.py]
   end

   subgraph Scripts[Automation]
      CLI[Python scripts \n scripts/main_menu.py]
      Utils[scripts/utils/*]
   end

   subgraph Google[Google Services]
      Sheets[Google Sheets]
      Drive[Google Drive]
   end

   SMTP[SMTP Mail Server]
   Templates[DOCX & HTML templates]
   Output[output/ (PDFs)]

   FE -->|calls| APINode
   APINode -->|reads/writes| Sheets
   CLI -->|reads/writes| Sheets
   CLI -->|uploads| Drive
   CLI -->|generates| Output
   Templates -->|used by| CLI
   CLI -->|sends via| SMTP
   APINode -->|invokes| CLI
   Utils -->|helpers| CLI
   FE -->|uploads/downloads| Drive

   classDef external fill:#f9f,stroke:#333,stroke-width:1px;
   class Sheets,Drive,SMTP external;
```


### Prerequisites
- Python 3.8+
- Node.js (for the frontend)
- Google API credentials for Google Sheets access
- SMTP configuration for email sending

### Installation (Backend)

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd SwipeGen-Automation
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the backend:**
   - Update `config.json` with your email and SMTP settings:
     ```json
     {
       "email": "your-email@gmail.com",
       "smtp_server": "smtp.gmail.com",
       "smtp_port": 587
     }
     ```

4. **Set up Google API credentials:**
   - Place your `credentials.json` and `service_account.json` files in the `scripts/` directory

5. **Run the backend CLI:**
   ```bash
   cd scripts
   python main_menu.py
   ```

### Frontend (optional)

The repository contains a Vite + React frontend in the `frontend/` folder. To run it:

```bash
cd frontend
npm install
npm run dev
```

The frontend communicates with the backend via the project's service APIs (see `frontend/src/services`).

### Backend API (FastAPI)

A minimal FastAPI app is provided in `api.py`. Install dependencies and run the API with Uvicorn for development or Gunicorn+Uvicorn workers for production.

Development:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Production (Gunicorn + Uvicorn workers):
```bash
gunicorn -k uvicorn.workers.UvicornWorker api:app -w 4 -b 0.0.0.0:8000
```

Extend `api.py` to call internal script functions (via safe, explicit mappings) rather than executing shell commands.

## 📋 Main Menu Options

The application presents a menu-driven interface with the following workflow options:

1. **📝 View & Shortlist Candidate Registrations** - Review and filter candidate data
2. **📧 Send Interview Invites** - Distribute interview invitations to shortlisted candidates
3. **📊 Generate Recruitment Summary Report** - Create comprehensive recruitment metrics
4. **✅ Update Hired Candidates** - Mark candidates as hired post-interview
5. **📩 Send Offer Letter Details Request** - Request required documents from hired candidates
6. **📄 Generate Offer Letters** - Create PDF offer letters
7. **✉️ Send Offer Letters** - Distribute offer letters and update status
8. **🎓 Generate Certificates** - Create completion certificates
9. **🏁 Send Completion Emails** - Send completion notifications and finalize records
0. **🚪 Exit** - Close the application

## ⚙️ Configuration
This project supports both simple `config.json` configuration and environment-based configuration using a `.env` file for sensitive values.

### config.json (optional)
```json
{
   "email": "your-email@gmail.com",
   "smtp_server": "smtp.gmail.com",
   "smtp_port": 587
}
```

### Environment variables (`.env`)
The CLI scripts expect an environment file with Google Sheets URLs, Drive folder IDs and SMTP settings. A working example exists at `scripts/.env`.

Key variables used by the scripts and API (from `scripts/.env`):

- `SENDER_EMAIL` — SMTP login email used to send messages.
- `SENDER_PASSWORD` — SMTP app password or credential (keep secret).
- `SMTP_PORT` — SMTP port (usually `587`).
- `WEBSITE_URL`, `INSTAGRAM_URL`, `LINKEDIN_URL`, `GOOGLE_SEARCH_URL` — optional links for templates.
- `REGISTRATION_SHEET_URL` — Google Sheet URL used for registrations.
- `INTERVIEW_RESPONSE_SHEET_URL` — Sheet for interview responses.
- `OFFER_DETAILS_SHEET_URL` — Sheet collecting offer details.
- `CERTIFICATES_DRIVE_FOLDER_ID` — Google Drive folder ID for certificates.
- `OFFER_LETTERS_DRIVE_FOLDER_ID` — Google Drive folder ID for offer letters.
- `COMPANY_NAME` — Company name to inject into templates.
- `EMAIL_SIGNATURE` — Default signature for outgoing emails.
- `OFFER_TEMPLATE_NAME`, `CERT_TEMPLATE_NAME` — template file names in `scripts/templates/`.

Notes:
- The provided FastAPI app (`api.py`) reads DOTENV from `backend/.env` by default (see `api.py`). The CLI scripts use `scripts/.env`. If you run the API, either create `backend/.env` (a copy of `scripts/.env`) or update `api.py` to point to `scripts/.env`.
- Never commit secrets (`SENDER_PASSWORD`, service account JSON) to source control.

### Email Templates
All email templates are located in the `scripts/templates/` directory and can be customized:
- `interview_email_template.html` - Interview invitation format
- `offer_email_template.html` - Offer letter email format
- `offer_details_template.html` - Offer details request format
- `completion_email_template.html` - Completion notification format
- `offer_template.docx`, `Completion_Certificate.docx` - DOCX templates used for generating documents

### Backend Scripts Overview
The `scripts/` directory contains a set of Python utilities and CLI entry points. Important files:

- `main_menu.py` — CLI menu to run common operations interactively.
- `view_shortlist.py` — Inspect and shortlist candidates from the registration sheet.
- `send_invites.py` — Send interview invite emails to shortlisted candidates.
- `send_offer_letters.py` — Attach and send offer PDFs via email.
- `generate_offers.py` — Create offer letters from templates (DOCX → PDF).
- `generate_certificates.py` — Create completion certificates from templates.
- `generate_summary.py` — Produce recruitment summary reports.
- `update_hired.py` — Mark candidates as hired and update sheets.
- `send_details_req.py` — Request missing details from candidates (documents, confirmations).
- `send_completion.py` — Send completion certificates and final notifications.
- `sent_history.json` — Tracks sent emails and documents for audit purposes.

Utility modules are under `scripts/utils/` and include helpers for Google Sheets (`sheets_helper.py`), Drive operations (`drive_helper.py`), PDF/DOCX inspection and rendering, and QR utilities used in templates.

### API Reference (FastAPI)
The repository includes a small FastAPI application (`api.py`) that exposes the core operations for integration with the frontend or other services. Example endpoints:

- `GET /health` — Basic service health.
- `GET /info` — Project metadata.
- `POST /trigger/{task}` — Lightweight task trigger (allowed tasks: `generate_offers`, `generate_certificates`).
- `GET /api/health` — API health check.
- `GET /api/candidates` — List candidates. Query params: `status`, `search`.
- `GET /api/candidates/{row_id}` — Get candidate row details (by sheet row number).
- `PUT /api/candidates/{row_id}/status` — Update candidate `Status` column. JSON body: `{"status":"shortlisted"}`.
- `POST /api/candidates` — Append a new candidate. Payload keys: `name`, `email`, `college`, `role`, `cgpa`, `resume_link`.
- `GET /api/settings` — Read current `.env` configuration values used by the API.
- `POST /api/settings` — Update allowed settings in the `.env` file (writes to the DOTENV path used by the API).
- `POST /api/settings/test-sheet` — Verify a Google Sheet URL and return headers.

Example: list all shortlisted candidates

```bash
curl 'http://localhost:8000/api/candidates?status=shortlisted'
```

Running the API (development):

```bash
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Security note: `api.py` uses a service account JSON file referenced by `backend/service_account.json`. Ensure this file exists and is protected. The API intentionally does not execute arbitrary shell commands — extend it by mapping allowed task names to internal function calls.

### Frontend
The frontend is a Vite + React application in the `frontend/` folder. Key points:

- Install and run locally:

```bash
cd frontend
npm install
npm run dev
```

- The frontend calls the API endpoints described above (see `frontend/src/services` for fetch wrappers).

### Running the CLI (scripts)
Use the interactive menu:

```bash
cd scripts
python main_menu.py
```

Or run specific scripts directly, e.g.:

```bash
python generate_offers.py
python send_offer_letters.py
```

### Troubleshooting
- If API cannot read `.env` values, ensure `backend/.env` exists (or update `api.py` to use `scripts/.env`).
- If Google Sheets access fails, verify the service account JSON path and that the service account has access to the sheet.
- For SMTP issues, confirm `SENDER_EMAIL` and `SENDER_PASSWORD` are correct and that less-secure access or app passwords are configured.


## 📊 Data Management

- **sent_history.json** - Logs all sent communications for audit trail
- **credentials.json** - Google API authentication (sensitive - not tracked in git)
- **service_account.json** - Service account credentials (sensitive - not tracked in git)

## 🔒 Security Notes

The following files are intentionally excluded from version control:
- `credentials.json` - Contains API keys
- `service_account.json` - Contains service account credentials
- `__pycache__/` - Python cache files

Never commit these files to the repository. Always keep credentials secure and use environment variables in production.

## 🛠️ Development

### Project Dependencies
All required packages are listed in `requirements.txt`. Install them using:
```bash
pip install -r requirements.txt
```

### Typical Workflow
1. Candidates register or submit resumes
2. HR reviews and shortlists candidates (Option 1)
3. Interview invites are sent (Option 2)
4. HR updates candidates marked as hired (Option 4)
5. Offer letter details are requested (Option 5)
6. Offer letters are generated (Option 6) and sent (Option 7)
7. Upon completion, certificates are generated (Option 8)
8. Completion emails are sent (Option 9)
9. Reports can be generated at any point (Option 3)

## 📄 Output Files

- **Certificates** - Generated in `output/certificates/`
- **Offer Letters** - Generated in `output/offer_letters/`
- **Reports** - Generated and optionally saved for analysis

## 🤝 Contributing

For contributions or improvements:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License. If this repository should be proprietary, update the license file accordingly.

## 👥 Ownership

This project is owned and managed by the project owner.

## 📞 Support

For issues, questions, or feature requests, please contact the development team or create an issue in the repository.

---

**Last Updated:** 2026-07-09  
**Version:** 1.0.0
