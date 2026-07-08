import os
import re
import smtplib
import gspread
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# ANSI Color Codes
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class CompletionEmailSender:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))
        
        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        self.images_dir = os.path.join(self.script_dir, "images") 
        self.cert_folder = os.path.join(self.script_dir, "output", "certificates")
        
        # --- FIXED URL LOGIC ---
        # Try specific Cert sheet first, otherwise fallback to Registration sheet
        self.sheet_url = os.getenv("CERTIFICATE_SHEET_URL")
        if not self.sheet_url:
            self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")

        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.template_path = os.path.join(self.script_dir, "templates", "completion_email_template.html")
        
        self.sheet_instance = None
        self.server = None

        self.local_images = {
            "logo_url": "logo.png",
            "ig_icon": "instagram.png",
            "li_icon": "linkedin.png",
            "google_icon": "google.png"
        }

        self.social_links = {
            "web_link": os.getenv("WEBSITE_URL", "https://www.hr-automation.in"),
            "ig_link": os.getenv("INSTAGRAM_URL", "#"),
            "li_link": os.getenv("LINKEDIN_URL", "#"),
            "google_link": os.getenv("GOOGLE_SEARCH_URL", "#"),
            "logo_url": "cid:logo_url",
            "ig_icon": "cid:ig_icon",
            "li_icon": "cid:li_icon",
            "google_icon": "cid:google_icon"
        }

    def connect(self):
        print(f"{Y}⏳ Connecting to Google Sheets...{W}")
        
        if not self.sheet_url:
            print(f"{R}❌ Error: No Sheet URL found in .env (Checked CERTIFICATE_SHEET_URL and REGISTRATION_SHEET_URL){W}")
            return False

        try:
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
                        target_sheet = sheet
                        break
            
            self.sheet_instance = target_sheet if target_sheet else spreadsheet.get_worksheet(0)
            print(f"{G}✅ Connected to Tab: {self.sheet_instance.title}{W}")
            return True
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}")
            return False

    def fetch_ready_candidates(self):
        try:
            data = self.sheet_instance.get_all_values()
            if not data: return []
            
            headers = [str(h).strip().lower() for h in data[0]]
            
            try:
                status_idx = next(i for i, h in enumerate(headers) if "status" in h)
                email_idx = next((i for i, h in enumerate(headers) if any(x in h for x in ["email", "e-mail"])), None)
                name_idx = next((i for i, h in enumerate(headers) if any(x in h for x in ["name", "student"])), None)

                if email_idx is None or name_idx is None:
                    print(f"{R}❌ Error: Could not find 'Name' or 'Email' columns.{W}")
                    return []
            except Exception as e:
                print(f"{R}❌ Header Error: {e}{W}")
                return []

            candidates = []
            for i, row in enumerate(data[1:], 1):
                status = row[status_idx].strip() if len(row) > status_idx else ""
                
                # --- FILTER: LOOK FOR 'CERTIFICATE GENERATED' ---
                if "certificate generated" in status.lower():
                    name = row[name_idx].strip() if len(row) > name_idx else "Candidate"
                    email = row[email_idx].strip() if len(row) > email_idx else ""
                    if email:
                        candidates.append({'Name': name, 'Email': email, '_row': i+1})
            
            return candidates
        except Exception as e:
            print(f"{R}Error fetching rows: {e}{W}")
            return []

    def attach_image(self, msg, filename, content_id):
        file_path = os.path.join(self.images_dir, filename)
        if not os.path.exists(file_path): return
        try:
            with open(file_path, 'rb') as f:
                image = MIMEImage(f.read())
            image.add_header('Content-ID', f'<{content_id}>') 
            image.add_header('Content-Disposition', 'inline', filename=filename)
            msg.attach(image)
        except: pass

    def get_certificate_path(self, full_name, email):
        # 1. Try exact name match first
        safe_name = "".join([c if c.isalnum() else "_" for c in full_name.split()[0]])
        email_prefix = email.split('@')[0] if email else "no_email"
        filename = f"Cert_{safe_name}_{email_prefix}.pdf"
        exact_path = os.path.join(self.cert_folder, filename)
        
        if os.path.exists(exact_path):
            return exact_path, filename
            
        # 2. Fallback: Search folder for partial match
        first_name = full_name.split()[0].lower()
        for file in os.listdir(self.cert_folder):
            if file.lower().endswith(".pdf") and first_name in file.lower():
                 return os.path.join(self.cert_folder, file), file
        
        return exact_path, filename

    def send_email(self, candidate):
        name = candidate['Name']
        email = candidate['Email']
        
        cert_path, cert_filename = self.get_certificate_path(name, email)
        if not os.path.exists(cert_path):
            print(f"{R}   ❌ Certificate PDF missing for {name}{W}")
            return False

        try:
            msg = MIMEMultipart('related')
            msg['From'] = self.sender_email
            msg['To'] = email
            msg['Subject'] = "Congratulations on your Completion! - HR-Automation"

            with open(self.template_path, 'r', encoding='utf-8') as f:
                body_html = f.read()
            
            body_html = body_html.replace("{name}", name)
            for key, value in self.social_links.items():
                body_html = body_html.replace(f"{{{key}}}", value)
            
            msg.attach(MIMEText(body_html, 'html'))

            for cid_name, filename in self.local_images.items():
                self.attach_image(msg, filename, cid_name)

            with open(cert_path, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header('Content-Disposition', 'attachment', filename=cert_filename)
                msg.attach(attach)

            self.server.send_message(msg)
            return True
        except Exception as e:
            print(f"{R}   ❌ Email Failed: {e}{W}")
            return False

    def update_status(self, row_num):
        try:
            headers = self.sheet_instance.row_values(1)
            status_col = next(i for i, h in enumerate(headers, 1) if "status" in str(h).lower())
            self.sheet_instance.update_cell(row_num, status_col, "Internship Completed")
            return True
        except: return False

    def run(self):
        if not self.connect(): return
        
        candidates = self.fetch_ready_candidates()
        if not candidates:
            print(f"\n{G}✅ No 'Certificate Generated' candidates waiting.{W}")
            return

        print(f"\n{B}📧 --- Completion Email Sender ---{W}")
        print(f"{Y}🔍 Found {len(candidates)} ready to receive certificates.{W}")
        
        try:
            self.server = smtplib.SMTP('smtp.gmail.com', 587)
            self.server.starttls()
            self.server.login(self.sender_email, self.sender_password)
        except Exception as e:
            print(f"{R}❌ SMTP Login Failed: {e}{W}")
            return

        for c in candidates:
            print(f"\n{B}Candidate: {Y}{c['Name']}{W} ({c['Email']})")
            choice = input(f"{G}1. Send{W} | {Y}2. Skip{W} | {R}3. Exit{W}\n👉 Action: ").strip()
            
            if choice == '1':
                print(f"{Y}📤 Sending...{W}", end=" ")
                if self.send_email(c):
                    print(f"{G}✅ Sent!{W}", end=" ")
                    if self.update_status(c['_row']):
                        print(f"{G}(Status Updated -> 'Internship Completed'){W}")
                    else:
                        print(f"{R}(Status Update Failed){W}")
                else:
                    print(f"{R}❌ Failed.{W}")
            elif choice == '2': continue
            elif choice == '3': break
        
        self.server.quit()
        print(f"\n{G}Task Finished.{W}")

def main():
    CompletionEmailSender().run()

if __name__ == "__main__":
    main()