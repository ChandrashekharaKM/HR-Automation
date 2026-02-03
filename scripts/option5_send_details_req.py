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
        
        # Load Social Links & Images from .env
        self.placeholders = {
            "web_link": os.getenv("WEBSITE_URL", "https://www.swipegen.in"),
            "ig_link": os.getenv("INSTAGRAM_URL", "#"),
            "li_link": os.getenv("LINKEDIN_URL", "#"),
            "google_link": os.getenv("GOOGLE_SEARCH_URL", "#"),
            "logo_url": os.getenv("SWIPEGEN_LOGO_URL", ""),
            "ig_icon": os.getenv("INSTAGRAM_ICON_URL", "https://cdn-icons-png.flaticon.com/512/174/174855.png"),
            "li_icon": os.getenv("LINKEDIN_ICON_URL", "https://cdn-icons-png.flaticon.com/512/174/174857.png"),
            "google_icon": os.getenv("GOOGLE_ICON_URL", "https://cdn-icons-png.flaticon.com/512/300/300221.png")
        }
        
        self.worksheet = None
        self.sent_list = self.load_history()

    def connect(self):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            
            # Open Sheet
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
            data = self.worksheet.get_all_values()
            if not data: return []
            
            headers = [str(h).strip().lower() for h in data[0]]
            
            try:
                status_idx = next(i for i, h in enumerate(headers) if "status" in h)
                email_idx = next(i for i, h in enumerate(headers) if "email" in h)
                name_idx = next(i for i, h in enumerate(headers) if "name" in h)
            except StopIteration:
                print(f"{R}❌ Error: Columns missing.{W}")
                return []

            pending_candidates = []
            print(f"{Y}⏳ Scanning rows...{W}")

            for i, row in enumerate(data[1:], 1):
                status = row[status_idx].strip() if len(row) > status_idx else ""
                email = row[email_idx].strip() if len(row) > email_idx else ""
                name = row[name_idx].strip() if len(row) > name_idx else "Candidate"
                
                if status.lower() == "hired":
                    if email in self.sent_list:
                        print(f"   ⏩ Skipping {name} - {C}Already Sent{W}")
                    else:
                        cand_dict = {'Name': name, 'Email': email, '_row': i+1}
                        pending_candidates.append(cand_dict)
            
            return pending_candidates

        except Exception as e:
            print(f"{R}Error: {e}{W}"); return []

    def send_single_email(self, name, email):
        if not self.sender_email or not self.sender_password: 
            print(f"{R}❌ Error: Check .env{W}"); return False
            
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            subject = "Congratulations! Next Steps for your Offer Letter - SwipeGen"
            template_path = os.path.join(self.base_dir, "templates", "offer_details_template.html")
            
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    raw_html = f.read()
                    
                    # 1. Replace Name
                    body = raw_html.replace("{name}", name).replace("{NAME}", name)
                    
                    # 2. Replace Social Links & Logos (The Fix)
                    for key, value in self.placeholders.items():
                        # Using simple string replace for HTML
                        body = body.replace(f"{{{key}}}", str(value))
            else:
                body = f"Hi {name},\n\nCongratulations! Please check the portal."

            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = email
            msg['Subject'] = subject
            
            if "<html" in body:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
                
            server.sendmail(self.sender_email, email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"{R}❌ SMTP Error: {e}{W}"); return False

def main():
    sender = OfferDetailsSender()
    if not sender.connect(): return
    
    print(f"\n{C}{'='*80}\n           OPTION 5: SEND OFFER DETAILS (LOCAL TRACKING)\n{'='*80}{W}")
    
    candidates = sender.fetch_pending_candidates()
    
    if not candidates:
        print(f"\n{G}✅ No NEW 'Hired' candidates.{W}"); return
    
    print(f"\n{B}--- Found {len(candidates)} Pending ---{W}")
    
    for c in candidates:
        name = c['Name']
        email = c['Email']
        print(f"\n{B}Candidate:{W} {name} | {email}")
        print(f"{G}1. Send{W} | {Y}2. Skip{W} | {R}3. Exit{W}")
        choice = input("👉 Action: ").strip()
        
        if choice == '1':
            print(f"{Y}📤 Sending...{W}", end=" ")
            if sender.send_single_email(name, email):
                sender.save_history(email)
                print(f"{G}✅ Sent!{W}")
            else: print(f"{R}❌ Failed.{W}")
        elif choice == '3': return

if __name__ == "__main__":
    main()