import os
import re
import smtplib
import gspread
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# ANSI Color Codes
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class InterviewInviter:
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(dotenv_path)
        self.creds_file = os.path.join(os.path.dirname(__file__), "service_account.json")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.google_form_url = "https://forms.gle/zivKMBVxaRLrPhDGA"
        self.worksheet = None

    def connect(self):
        try:
            match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', self.sheet_url)
            if not match: return False
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            self.worksheet = client.open_by_key(match.group(1)).get_worksheet(0)
            return True
        except Exception as e:
            print(f"{R}Connection Error: {e}{W}")
            return False

    def _get_template(self, name):
        """Reads the template from the templates folder"""
        try:
            template_path = os.path.join(os.path.dirname(__file__), "templates", "interview_template.txt")
            with open(template_path, "r") as file:
                content = file.read()
            return content.format(name=name, form_url=self.google_form_url)
        except Exception as e:
            print(f"{R}Error reading template: {e}{W}")
            return f"Hi {name}, please confirm your interview here: {self.google_form_url}"

    def fetch_by_status(self, status_text):
        all_records = self.worksheet.get_all_records()
        return [dict(row, _row=i+2) for i, row in enumerate(all_records) 
                if str(row.get('Status', '')).strip() == status_text]

    def display_candidates(self, candidates, title):
        print(f"\n{C}{'='*80}\n {title} ({len(candidates)})\n{'='*80}{W}")
        print(f"{'SL No.':<8} | {'Email':<30} | {'Resume Link'}")
        print("-" * 80)
        for i, c in enumerate(candidates, 1):
            email = c.get('Email address') or c.get('Email') or "N/A"
            resume = c.get('Resume Link') or c.get('Resume') or "N/A"
            print(f"{i:<8} | {email:<30} | {C}{resume}{W}")
        print("-" * 80)

    def send_bulk_emails(self, candidates):
        if not self.sender_email or not self.sender_password:
            print(f"{R}Credentials missing!{W}"); return
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            headers = self.worksheet.row_values(1)
            status_col = headers.index("Status") + 1
            print(f"\n{Y}🚀 Starting email broadcast...{W}")
            for c in candidates:
                name = c.get('Name') or c.get('Full Name') or "Candidate"
                email = c.get('Email address') or c.get('Email')
                if not email: continue
                msg = MIMEMultipart()
                msg['From'] = self.sender_email
                msg['To'] = email
                msg['Subject'] = "SwipeGen - Interview Confirmation"
                body = self._get_template(name)
                msg.attach(MIMEText(body, 'plain'))
                try:
                    server.sendmail(self.sender_email, email, msg.as_string())
                    self.worksheet.update_cell(c['_row'], status_col, "Invited for Interview")
                    print(f"{G}✅ Sent & Updated: {email}{W}")
                except Exception as e:
                    print(f"{R}❌ Failed for {email}: {e}{W}")
                time.sleep(1.5)
            server.quit()
        except Exception as e:
            print(f"{R}SMTP Error: {e}{W}")

def main():
    inviter = InterviewInviter()
    if not inviter.connect(): return
    while True:
        print(f"\n{B}--- SWIPEGEN INTERVIEW INVITER ---{W}")
        print(f"{G}1. Shortlisted (Send Invites){W}")
        print(f"{R}2. Not Shortlisted (View List){W}")
        print(f"{Y}3. Exit{W}")
        choice = input(f"\n👉 {C}Select option: {W}")
        if choice == '1':
            candidates = inviter.fetch_by_status("Resume Shortlisted")
            if not candidates:
                print(f"{R}❌ No shortlisted student found.{W}")
                continue
            inviter.display_candidates(candidates, "SHORTLISTED CANDIDATES")
            action = input(f"\n👉 {C}Choice (all / range e.g. 1-5 / c): {W}").strip().lower()
            if action == 'all':
                inviter.send_bulk_emails(candidates)
            elif '-' in action:
                try:
                    start, end = map(int, action.split('-'))
                    inviter.send_bulk_emails(candidates[start-1:end])
                except: print(f"{R}Invalid range{W}")
        elif choice == '2':
            candidates = inviter.fetch_by_status("Not Shortlisted")
            if not candidates:
                print(f"{R}❌ No not-shortlisted students found.{W}")
            else:
                inviter.display_candidates(candidates, "NOT SHORTLISTED")
        elif choice == '3': break

if __name__ == "__main__":
    main()