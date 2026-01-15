import os
import smtplib
import gspread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# ANSI colors
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class OfferEmailSender:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))

        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        self.reg_sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        
        # Social Links from .env
        self.ig_link = os.getenv("INSTAGRAM_URL", "#")
        self.li_link = os.getenv("LINKEDIN_URL", "#")
        self.web_link = os.getenv("WEBSITE_URL", "#")

        self.template_path = os.path.join(self.script_dir, "templates", "offer_email_template.html")
        self.offer_dir = os.path.join(self.script_dir, "output", "offer_letters")
        self.worksheet = None

    def connect(self):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            self.worksheet = client.open_by_url(self.reg_sheet_url).get_worksheet(0)
            return True
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}"); return False

    def fetch_data_safely(self):
        data = self.worksheet.get_all_values()
        if not data: return []
        headers = [h.strip() if h.strip() else f"col_{i}" for i, h in enumerate(data[0])]
        return [dict(zip(headers, row), _row=i+1) for i, row in enumerate(data[1:], 1)]

    def send_offer_email(self, candidate, manual_data):
        full_name = (candidate.get("Full Name(as per Aadhar/PAN)") or candidate.get("Name") or "Candidate").strip()
        recipient_email = (candidate.get("Email address") or candidate.get("Email")).strip()
        
        safe_name = "".join([c if c.isalnum() else "_" for c in full_name])
        pdf_path = os.path.join(self.offer_dir, f"Offer_{safe_name}.pdf")

        if not os.path.exists(pdf_path):
            print(f"{R}❌ PDF missing for {full_name}. Run Option 6 first.{W}")
            return False

        msg = MIMEMultipart()
        msg['From'] = f"Team SwipeGen <{self.sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = "Journey with SwipeGen begins now!"

        with open(self.template_path, "r", encoding="utf-8") as f:
            html_content = f.read().format(
                name=full_name.split()[0],
                role=manual_data['role'],
                start_date=manual_data['start_date'],
                ig_link=self.ig_link, li_link=self.li_link, web_link=self.web_link
            )
        msg.attach(MIMEText(html_content, 'html'))

        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename=Offer_{safe_name}.pdf")
            msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(self.sender_email, self.sender_password)
        server.sendmail(self.sender_email, recipient_email, msg.as_string())
        server.quit()
        return True

    def run_process(self):
        if not self.connect(): return
        records = self.fetch_data_safely()
        hired = [r for r in records if str(r.get("Status", "")).strip() == "Hired"]

        if not hired:
            print(f"{Y}⚠️ No candidates marked 'Hired' found.{W}"); return

        for candidate in hired:
            name = candidate.get("Full Name(as per Aadhar/PAN)") or candidate.get("Name")
            print(f"\n{B}Candidate: {Y}{name}{W}")
            if input(f"{C}Send HTML Offer Email? (y/n): {W}").lower() != 'y': continue

            m_role = input("💼 Role [Software Developer - Intern]: ") or "Software Developer - Intern"
            m_start = input("🗓️  Start Date [December 24, 2025]: ") or "December 24, 2025"

            if self.send_offer_email(candidate, {'role': m_role, 'start_date': m_start}):
                # Update status
                headers = self.worksheet.row_values(1)
                status_col = next(i for i, h in enumerate(headers, 1) if "status" in h.lower())
                self.worksheet.update_cell(candidate['_row'], status_col, "Internship Ongoing")
                print(f"{G}✅ Sent and status updated!{W}")

def main():
    OfferEmailSender().run_process()

if __name__ == "__main__":
    main()