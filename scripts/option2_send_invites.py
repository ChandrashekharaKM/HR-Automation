import os
import re
import smtplib
import gspread
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class InterviewInviter:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.base_dir, '..', '.env'))
        self.creds_file = os.path.join(self.base_dir, "service_account.json")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.google_form_url = "https://forms.gle/zivKMBVxaRLrPhDGA"
        self.worksheet = None
        # Ensure ALL these keys exist:
        self.social_links = {
            "web_link": os.getenv("WEBSITE_URL", "#"),
            "ig_link": os.getenv("INSTAGRAM_URL", "#"),
            "li_link": os.getenv("LINKEDIN_URL", "#"),
            "google_link": os.getenv("GOOGLE_SEARCH_URL", "#"), # Required by template
            
            "logo_url": os.getenv("SWIPEGEN_LOGO_URL", ""),
            "ig_icon": os.getenv("INSTAGRAM_ICON_URL", ""),
            "li_icon": os.getenv("LINKEDIN_ICON_URL", ""),
            "google_icon": os.getenv("GOOGLE_ICON_URL", "")     # Required by template
        }

    def connect(self):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            
            # Open by URL
            spreadsheet = client.open_by_url(self.sheet_url)

            # Smart Tab Detection using GID
            gid_match = re.search(r'gid=([0-9]+)', self.sheet_url)
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        self.worksheet = sheet
                        print(f"{G}✅ Connected to tab: {sheet.title}{W}")
                        return True
            
            # Fallback
            self.worksheet = spreadsheet.get_worksheet(0)
            print(f"{Y}⚠️ Using first tab: {self.worksheet.title}{W}")
            return True
        except Exception as e:
            print(f"{R}Connection Error: {e}{W}")
            return False

    def _get_template(self, name):
        try:
            template_path = os.path.join(self.base_dir, "templates", "interview_email_template.html")
            with open(template_path, "r", encoding="utf-8") as file:
                tpl = file.read()
                return tpl.format(name=name, form_url=self.google_form_url, **self.social_links)
        except Exception:
            return f"Hi {name}, please confirm your interview here: {self.google_form_url}"

    def fetch_by_status(self, status_text):
        all_records = self.worksheet.get_all_records()
        return [dict(row, _row=i+2) for i, row in enumerate(all_records) if str(row.get('Status', '')).strip() == status_text]

    def display_candidates(self, candidates, title):
        print(f"\n{C}{'='*80}\n {title} ({len(candidates)})\n{'='*80}{W}")
        print(f"{ 'SL No.':<8} | {'Email':<30} | {'Resume Link'}")
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
                msg.attach(MIMEText(self._get_template(name), 'html'))
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
        print(f"1. Shortlisted (Send Invites)")
        print(f"2. Not Shortlisted (View List)")
        print(f"3. Exit")
        choice = input(f"\n👉 {C}Select option: {W}")
        if choice == '1':
            candidates = inviter.fetch_by_status("Resume Shortlisted")
            if not candidates: print(f"{R}❌ No shortlisted student found.{W}"); continue
            inviter.display_candidates(candidates, "SHORTLISTED CANDIDATES")
            action = input(f"\n👉 {C}Choice (all / range 1-5 / c): {W}").strip().lower()
            if action == 'all': inviter.send_bulk_emails(candidates)
            elif '-' in action:
                try:
                    s, e = map(int, action.split('-'))
                    inviter.send_bulk_emails(candidates[s-1:e])
                except: print(f"{R}Invalid range{W}")
        elif choice == '2':
            candidates = inviter.fetch_by_status("Not Shortlisted")
            inviter.display_candidates(candidates, "NOT SHORTLISTED") if candidates else print(f"{R}Empty list{W}")
        elif choice == '3': break

if __name__ == "__main__":
    main()