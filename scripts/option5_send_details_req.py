import os
import re
import smtplib
import gspread
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class OfferDetailsSender:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.base_dir, '..', '.env'))
        self.history_file = os.path.join(self.base_dir, "sent_history.json")
        self.creds_file = os.path.join(self.base_dir, "service_account.json")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.worksheet = None
        self.sent_list = self.load_history()

    def connect(self):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_url(self.sheet_url)
            
            gid_match = re.search(r'gid=([0-9]+)', self.sheet_url)
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        self.worksheet = sheet
                        return True
            self.worksheet = spreadsheet.get_worksheet(0)
            return True
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}"); return False

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f: return json.load(f)
            except: return []
        return []

    def save_history(self, email):
        if email not in self.sent_list:
            self.sent_list.append(email)
            with open(self.history_file, 'w') as f: json.dump(self.sent_list, f)

    def fetch_pending_candidates(self):
        try:
            data = self.worksheet.get_all_records()
            return [dict(r, _row=i+2) for i, r in enumerate(data) if str(r.get('Status','')).strip()=="Hired" and r.get('Email address') not in self.sent_list]
        except Exception as e:
            print(f"{R}Error: {e}{W}"); return []

    def send_single_email(self, name, email):
        if not self.sender_email or not self.sender_password: return False
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            template_path = os.path.join(self.base_dir, "templates", "offer_details_template.html")
            with open(template_path, "r", encoding="utf-8") as f: body = f.read().format(name=name)
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = email
            msg['Subject'] = "Congratulations! Next Steps for your Offer Letter - SwipeGen"
            msg.attach(MIMEText(body, 'plain'))
            server.sendmail(self.sender_email, email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"{R}SMTP Error: {e}{W}"); return False

def main():
    sender = OfferDetailsSender()
    if not sender.connect(): return
    print(f"\n{C}{'='*80}\n           OPTION 5: SEND OFFER DETAILS (LOCAL TRACKING)\n{'='*80}{W}")
    candidates = sender.fetch_pending_candidates()
    if not candidates: print(f"\n{G}✅ No pending candidates.{W}"); return
    
    for c in candidates:
        name = c.get('Name') or c.get('Full Name') or "N/A"
        email = c.get('Email address') or c.get('Email')
        print(f"\n{B}Candidate:{W} {name} | {email}")
        print(f"{G}1. Send{W} | {Y}2. Skip{W} | {R}3. Exit{W}")
        choice = input("👉 Action: ").strip()
        if choice == '1':
            if sender.send_single_email(name, email):
                sender.save_history(email)
                print(f"{G}✅ Sent & Saved.{W}")
            else: print(f"{R}❌ Failed.{W}")
        elif choice == '3': return

if __name__ == "__main__":
    main()