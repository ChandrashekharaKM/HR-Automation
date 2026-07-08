# 🚀 HR-Automation System

A comprehensive HR automation system designed to streamline the entire recruitment and internship workflow—from candidate shortlisting to completion certificate generation.

## 📋 Overview

HR-Automation is a Python-based automation tool that automates critical HR processes including:

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
HR-Automation/
├── README.md                          # Project documentation
├── config.json                        # Configuration settings
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
│
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

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google API credentials for Google Sheets access
- SMTP configuration for email sending

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd HR-Automation
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application:**
   - Update `config.json` with your email and SMTP settings:
     ```json
     {
       "email": "your-email@gmail.com",
       "smtp_server": "smtp.gmail.com",
       "smtp_port": 587
     }
     ```

4. **Set up Google API credentials:**
   - Place your `credentials.json` file in the `scripts/` directory
   - Place your `service_account.json` file in the `scripts/` directory

5. **Run the application:**
   ```bash
   cd scripts
   python main_menu.py
   ```

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

### config.json
```json
{
  "email": "your-email@gmail.com",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

### Email Templates
All email templates are located in the `templates/` directory and can be customized:
- `interview_template.txt` - Interview invitation format
- `offer_email_template.html` - Offer letter email format
- `offer_details_template.txt` - Offer details request format
- `completion_email_template.html` - Completion notification format

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

This project is licensed under the MIT License.

## 📝 License

This project is proprietary and confidential.

## 👥 Ownership

This project is owned and managed by the project owner.

## 📞 Support

For issues, questions, or feature requests, please contact the development team or create an issue in the repository.

---

**Last Updated:** January 2026  
**Version:** 1.0.0
