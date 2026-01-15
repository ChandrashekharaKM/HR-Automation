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

# ANSI Color Codes
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class OfferDetailsSender:
    def __init__(self):
        # Setup Paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        dotenv_path = os.path.join(self.base_dir, '..', '.env')
        load_dotenv(dotenv_path)
        
        # History File Path (This is the "Different Approach")
        self.history_file = os.path.join(self.base_dir, "sent_history.json")
        
        # Credentials
        self.creds_file = os.path.join(self.base_dir, "credentials.json")
        if not os.path.exists(self.creds_file):
             self.creds_file = os.path.join(self.base_dir, "..", "service_account.json")

        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.worksheet = None
        self.sent_list = self.load_history()

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
            print(f"{R}❌ Connection Error: {e}{W}")
            return False

    # --- NEW: HISTORY TRACKING FUNCTIONS ---
    def load_history(self):
        """Loads the list of emails that have already been processed."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_history(self, email):
        """Saves a new email to the processed list."""
        if email not in self.sent_list:
            self.sent_list.append(email)
            with open(self.history_file, 'w') as f:
                json.dump(self.sent_list, f)

    def fetch_pending_candidates(self):
        """Fetch candidates who are 'Hired' AND not in our local history file"""
        try:
            data = self.worksheet.get_all_values()
            if not data: return []
            
            raw_headers = data[0]
            headers = [h.strip() for h in raw_headers]
            rows = data[1:]
            pending_list = []
            
            for i, row_vals in enumerate(rows):
                row_dict = {}
                for idx, header in enumerate(headers):
                    if idx < len(row_vals):
                        row_dict[header] = row_vals[idx]
                    else:
                        row_dict[header] = ""

                # --- LOGIC: Check Status 'Hired' vs Local History ---
                status = str(row_dict.get('Status', '')).strip()
                email = str(row_dict.get('Email address', '') or row_dict.get('Email', '')).strip()

                # If Hired AND Email is NOT in our local 'sent_list'
                if status == "Hired" and email and email not in self.sent_list:
                    row_dict['_row'] = i + 2
                    pending_list.append(row_dict)
            
            return pending_list
        except Exception as e:
            print(f"{R}❌ Error fetching candidates: {e}{W}")
            return []

    def _get_template(self, name):
        try:
            template_path = os.path.join(self.base_dir, "templates", "offer_details_template.txt")
            with open(template_path, "r", encoding="utf-8") as file:
                return file.read().format(name=name)
        except Exception as e:
            print(f"{R}❌ Error reading template: {e}{W}")
            return None

    def send_single_email(self, name, email):
        if not self.sender_email or not self.sender_password:
            print(f"{R}❌ Email credentials missing in .env{W}"); return False

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            body = self._get_template(name)
            if not body: return False

            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = email
            msg['Subject'] = "Congratulations! Next Steps for your Offer Letter - SwipeGen"
            msg.attach(MIMEText(body, 'plain'))

            server.sendmail(self.sender_email, email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"{R}❌ SMTP Error: {e}{W}")
            return False

def main():
    sender = OfferDetailsSender()
    if not sender.connect(): return

    print(f"\n{C}{'='*80}\n           OPTION 5: SEND OFFER DETAILS (LOCAL TRACKING)\n{'='*80}{W}")

    candidates = sender.fetch_pending_candidates()

    if not candidates:
        print(f"\n{G}✅ No pending candidates found (Checked against 'sent_history.json').{W}")
        return

    for c in candidates:
        name = c.get('Name') or c.get('Full Name') or "N/A"
        email = c.get('Email address') or c.get('Email') or "N/A"
        row_num = c.get('_row')
        
        print(f"\n{B}Candidate Info:{W}")
        print(f"Row {row_num} | Name: {Y}{name}{W} | Email: {C}{email}{W}")
        print("-" * 80)
        print(f"{G}1. Send Email{W}")
        print(f"{Y}2. Skip{W}")
        print(f"{R}3. Exit{W}")
        
        choice = input(f"\n👉 {C}Action for {name}: {W}").strip()

        if choice == '1':
            print(f"{Y}Sending email...{W}")
            if sender.send_single_email(name, email):
                print(f"{G}✅ Email sent to {name}!{W}")
                
                # --- SAVE TO LOCAL HISTORY ---
                print(f"{Y}Saving to local history...{W}")
                sender.save_history(email) 
                print(f"{G}✅ Saved. Will not prompt again.{W}")
            else:
                print(f"{R}❌ Failed to send email.{W}")
            
            time.sleep(1)
            
        elif choice == '2':
            print(f"{Y}⏭️  Skipped {name}{W}")
            continue
            
        elif choice == '3':
            print(f"\n{Y}Exiting...{W}")
            return
            
        else:
            print(f"{R}⚠️ Invalid choice, skipping...{W}")
    
    print(f"\n{G}✅ All pending candidates processed.{W}")

if __name__ == "__main__":
    main()