import os
import re
import smtplib
import gspread
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage # Required for local images
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class OfferDetailsSender:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.base_dir, '..', '.env'))
        
        self.history_file = os.path.join(self.base_dir, "sent_history.json")
        self.creds_file = os.path.join(self.base_dir, "service_account.json")
        self.images_dir = os.path.join(self.base_dir, "images") # Local images folder
        
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        
        self.worksheet = None
        self.sent_list = self.load_history()

        # 1. Map Placeholders to Local Filenames
        self.local_images = {
            "logo_url": "logo.png",
            "ig_icon": "instagram.png",
            "li_icon": "linkedin.png",
            "google_icon": "google.png"
        }

        # 2. Data for HTML Replacement (Using cid: for images)
        self.placeholders = {
            "web_link": os.getenv("WEBSITE_URL", "https://www.swipegen.in"),
            "ig_link": os.getenv("INSTAGRAM_URL", "#"),
            "li_link": os.getenv("LINKEDIN_URL", "#"),
            "google_link": os.getenv("GOOGLE_SEARCH_URL", "#"),
            
            # These point to the attachments we create later
            "logo_url": "cid:logo_url",
            "ig_icon": "cid:ig_icon",
            "li_icon": "cid:li_icon",
            "google_icon": "cid:google_icon"
        }

    def connect(self):
        try:
            print(f"{Y}⏳ Connecting to Google Sheets...{W}")
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            
            spreadsheet = client.open_by_url(self.sheet_url)
            gid_match = re.search(r'gid=([0-9]+)', self.sheet_url)
            
            target_sheet = None
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        target_sheet = sheet; break
            
            self.worksheet = target_sheet if target_sheet else spreadsheet.get_worksheet(0)
            print(f"{G}✅ Connected to Tab: {self.worksheet.title}{W}")
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
                print(f"{R}❌ Error: Required columns (Name, Email, Status) missing.{W}")
                return []

            pending_candidates = []
            
            for i, row in enumerate(data[1:], 1):
                status = row[status_idx].strip() if len(row) > status_idx else ""
                email = row[email_idx].strip() if len(row) > email_idx else ""
                name = row[name_idx].strip() if len(row) > name_idx else "Candidate"
                
                # Check 1: Must be Hired
                if status.lower() == "hired":
                    # Check 2: Must NOT be in history
                    if email in self.sent_list:
                        # Optional: Print skipped ones if debugging
                        # print(f"   ⏩ Skipping {name} (Already Sent)")
                        pass
                    else:
                        cand_dict = {'Name': name, 'Email': email, '_row': i+1}
                        pending_candidates.append(cand_dict)
            
            return pending_candidates

        except Exception as e:
            print(f"{R}Error fetching data: {e}{W}"); return []

    def attach_image(self, msg, filename, content_id):
        """Helper to attach local image with Content-ID"""
        file_path = os.path.join(self.images_dir, filename)
        if not os.path.exists(file_path):
            print(f"{Y}   ⚠️ Image missing: {filename}{W}")
            return

        try:
            with open(file_path, 'rb') as f:
                img_data = f.read()
            
            image = MIMEImage(img_data)
            image.add_header('Content-ID', f'<{content_id}>') 
            image.add_header('Content-Disposition', 'inline', filename=filename)
            msg.attach(image)
        except Exception as e:
            print(f"{R}   ❌ Failed to attach {filename}: {e}{W}")

    def send_single_email(self, name, email):
        if not self.sender_email or not self.sender_password: 
            print(f"{R}❌ Credentials missing in .env{W}"); return False
            
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            subject = "Congratulations! Next Steps for your Offer Letter - SwipeGen"
            
            # 1. Prepare Content
            template_path = os.path.join(self.base_dir, "templates", "offer_details_template.html")
            body = ""
            
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    raw_html = f.read()
                    # Replace Name
                    body = raw_html.replace("{name}", name).replace("{NAME}", name)
                    # Replace Links & Image CIDs
                    for key, value in self.placeholders.items():
                        body = body.replace(f"{{{key}}}", str(value))
            else:
                body = f"<p>Hi {name}, Congratulations! You are hired.</p>"

            # 2. Construct Email (Multipart/Related for inline images)
            msg = MIMEMultipart('related')
            msg['From'] = self.sender_email
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))

            # 3. Attach Images
            for cid_name, filename in self.local_images.items():
                self.attach_image(msg, filename, cid_name)
                
            # 4. Send
            server.sendmail(self.sender_email, email, msg.as_string())
            server.quit()
            return True

        except Exception as e:
            print(f"{R}❌ SMTP Error: {e}{W}"); return False

def main():
    sender = OfferDetailsSender()
    if not sender.connect(): return
    
    print(f"\n{C}{'='*80}\n           SEND OFFER DETAILS (Local Images & Tracking)\n{'='*80}{W}")
    
    candidates = sender.fetch_pending_candidates()
    
    if not candidates:
        print(f"\n{G}✅ No NEW 'Hired' candidates to email.{W}")
        return
    
    print(f"\n{Y}🔍 Found {len(candidates)} new Hired candidate(s).{W}")
    
    for c in candidates:
        name = c['Name']
        email = c['Email']
        print(f"\n{B}Candidate:{W} {name} | {email}")
        
        while True:
            choice = input(f"{G}1. Send{W} | {Y}2. Skip{W} | {R}3. Exit{W}\n👉 Action: ").strip()
            
            if choice == '1':
                print(f"{Y}📤 Sending...{W}", end=" ")
                if sender.send_single_email(name, email):
                    sender.save_history(email)
                    print(f"{G}✅ Sent!{W}")
                else: 
                    print(f"{R}❌ Failed.{W}")
                break
            elif choice == '2':
                print(f"{Y}⏩ Skipped.{W}")
                break
            elif choice == '3':
                print("Exiting...")
                return

if __name__ == "__main__":
    main()