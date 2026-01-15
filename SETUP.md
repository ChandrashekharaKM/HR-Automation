# Setup Guide for SwipeGen HR Automation

## 📋 Prerequisites

Before you begin, ensure you have:
- Python 3.8 or higher installed
- pip (Python package manager)
- Git installed
- A Gmail account with app-specific password
- Google Sheets API enabled
- Google Drive API enabled

## 🔧 Step-by-Step Setup

### 1. Clone the Repository
```bash
git clone https://github.com/NamanSinha786/SwipeGen_Automations.git
cd SwipeGen-Automation
```

### 2. Create a Virtual Environment (Recommended)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Google API Setup

#### Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project named "SwipeGen Automation"
3. Enable the following APIs:
   - Google Sheets API
   - Google Drive API

#### Create Service Account
1. Navigate to "Service Accounts" in the Google Cloud Console
2. Create a new service account
3. Create a key (JSON format) and save it as `scripts/service_account.json`
4. Share your Google Sheet with the service account email

#### Create OAuth 2.0 Credentials
1. Go to "OAuth consent screen" and configure it
2. Create OAuth 2.0 Client ID (Desktop application)
3. Download the credentials as JSON and save as `scripts/credentials.json`

### 5. Configuration

#### Update config.json
Edit `config.json` with your settings:
```json
{
  "email": "your-email@gmail.com",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

#### Gmail Setup
1. Go to [Gmail Account Security](https://myaccount.google.com/security)
2. Enable "2-Step Verification"
3. Create an "App password" for this application
4. Use this app password for SMTP authentication

### 6. Verify Installation
```bash
cd scripts
python main_menu.py
```

You should see the main menu with all options available.

## 📊 Google Sheets Setup

Your Google Sheet should have the following structure:

### Candidate Data Sheet
Columns should include:
- Email
- Name
- Resume Link
- Status (Shortlisted, Interview Invited, Hired, Offer Sent, Completed)
- Interview Date
- Result
- Offer Acceptance

## 🚀 First Run

1. Make sure you have candidate data in your Google Sheet
2. Run the application: `python main_menu.py`
3. Start with Option 1: View & Shortlist Candidates
4. Follow the workflow sequentially for best results

## 🔒 Security Checklist

- [ ] Never commit `credentials.json` or `service_account.json`
- [ ] Keep `config.json` with dummy values in git
- [ ] Use environment variables for sensitive data in production
- [ ] Regularly rotate your Google Cloud credentials
- [ ] Use app-specific passwords for Gmail (not your main password)
- [ ] Keep your email credentials secure

## 🆘 Troubleshooting

### "No module named 'google.auth'"
```bash
pip install --upgrade google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### "credentials.json not found"
Ensure you've downloaded the OAuth credentials and placed them in the `scripts/` directory.

### "SMTP Connection Failed"
- Verify your email and password in `config.json`
- Check that you're using an app-specific password (not your Gmail password)
- Ensure 2-Step Verification is enabled on your Gmail account

### "Permission Denied" on Google Sheets
- Share the Google Sheet with the service account email address
- Ensure the service account has Editor permissions

### "PDF Generation Failed"
- Ensure `reportlab` is installed: `pip install reportlab`
- Check that the `output/offer_letters/` directory exists

## 📞 Support

For additional help:
1. Check the main [README.md](README.md)
2. Review the inline documentation in each script
3. Check Google Cloud Console for any API errors

---

**Last Updated:** January 2026
