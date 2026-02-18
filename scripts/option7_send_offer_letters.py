import os
import re
import smtplib
import gspread
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage 
from email import encoders
from datetime import datetime, timedelta
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class OfferEmailSender:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))

        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        self.images_dir = os.path.join(self.script_dir, "images") 
        self.offer_dir = os.path.join(self.script_dir, "output", "offer_letters")
        
        self.reg_sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.template_path = os.path.join(self.script_dir, "templates", "offer_email_template.html")
        
        self.worksheet = None

        self.local_images = {
            "logo_url": "logo.png",
            "ig_icon": "instagram.png",
            "li_icon": "linkedin.png",
            "google_icon": "google.png"
        }

        self.social_links = {
            "web_link": os.getenv("WEBSITE_URL", "https://www.swipegen.in"),
            "ig_link": os.getenv("INSTAGRAM_URL", "#"),
            "li_link": os.getenv("LINKEDIN_URL", "#"),
            "google_link": os.getenv("GOOGLE_SEARCH_URL", "#"),
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
            
            spreadsheet = client.open_by_url(self.reg_sheet_url)
            gid_match = re.search(r'gid=([0-9]+)', self.reg_sheet_url)
            
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

    def fetch_data_safely(self):
        data = self.worksheet.get_all_values()
        if not data: return []
        headers = [h.strip() if h.strip() else f"col_{i}" for i, h in enumerate(data[0])]
        return [dict(zip(headers, row), _row=i+1) for i, row in enumerate(data[1:], 1)]

    def attach_image(self, msg, filename, content_id):
        file_path = os.path.join(self.images_dir, filename)
        if not os.path.exists(file_path): return
        try:
            with open(file_path, 'rb') as f: img_data = f.read()
            image = MIMEImage(img_data)
            image.add_header('Content-ID', f'<{content_id}>') 
            image.add_header('Content-Disposition', 'inline', filename=filename)
            msg.attach(image)
        except: pass

    def send_offer_email(self, candidate, manual_data):
        f_name = candidate.get("First Name") or candidate.get("Name")
        l_name = candidate.get("Last Name")
        full_name = f"{f_name} {l_name}".strip() if f_name and l_name else (f_name or "Candidate")
        
        recipient_email = (candidate.get("Email address") or candidate.get("Email")).strip()
        candidate_id = candidate.get("ID") or candidate.get("Roll No")
        
        # 1. Locate PDF
        safe_name = "".join([c if c.isalnum() or c == '_' else "_" for c in full_name])
        if candidate_id:
            safe_id = "".join([c if c.isalnum() else "" for c in candidate_id])
            pdf_filename = f"Offer_{safe_name}_{safe_id}.pdf"
        else:
            pdf_filename = f"Offer_{safe_name}.pdf"
            
        pdf_path = os.path.join(self.offer_dir, pdf_filename)
        
        # Fallback search
        if not os.path.exists(pdf_path):
            pdf_path_alt = os.path.join(self.offer_dir, f"Offer_{safe_name}.pdf")
            if os.path.exists(pdf_path_alt):
                pdf_path = pdf_path_alt
                pdf_filename = f"Offer_{safe_name}.pdf"
            else:
                print(f"{R}❌ PDF missing: {pdf_filename}. Run Generator first.{W}")
                return False

        # 2. Calculate Expiry Date
        start_date_str = manual_data['start_date']
        try:
            date_obj = datetime.strptime(start_date_str, "%B %d, %Y")
            expiry_obj = date_obj + timedelta(days=2)
            expiry_date_str = expiry_obj.strftime("%B %d, %Y")
        except:
            expiry_date_str = "2 days after start date"

        # 3. Build Email
        msg = MIMEMultipart('related')
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Journey with SwipeGen begins now!"

        with open(self.template_path, "r", encoding="utf-8") as f:
            html_content = f.read().format(
                name=full_name.split()[0],
                role=manual_data['role'],
                start_date=start_date_str,
                expiry_date=expiry_date_str,
                **self.social_links 
            )
        msg.attach(MIMEText(html_content, 'html'))

        for cid_name, filename in self.local_images.items():
            self.attach_image(msg, filename, cid_name)

        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={pdf_filename}")
            msg.attach(part)

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, recipient_email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"{R}SMTP Error: {e}{W}"); return False

    def run_process(self):
        if not self.connect(): return
        records = self.fetch_data_safely()
        
        # --- FIXED FILTER: LOOK FOR "HIRED" ---
        ready_list = [r for r in records if str(r.get("Status", "")).strip() == "Hired"]

        if not ready_list:
            print(f"{Y}⚠️ No candidates marked 'Hired' found.{W}")
            return

        print(f"\n{B}--- Found {len(ready_list)} Hired candidates ---{W}")

        for candidate in ready_list:
            name = candidate.get("First Name") or candidate.get("Name") or "Candidate"
            #email = candidate.get("Email") or "No Email"
            
            print(f"\n{B}Candidate: {Y}{name}{W} ({email})")
            choice = input(f"{G}1. Send{W} | {Y}2. Skip{W} | {R}3. Exit{W}\n👉 Action: ").strip()

            if choice == '1':
                m_role = "Software Developer - Intern"
                
                # Fetch Start Date or Default to Today
                sheet_start = candidate.get("Start Date") or candidate.get("Joining Date")
                if not sheet_start:
                    sheet_start = datetime.now().strftime("%B %d, %Y")
                
                print(f"{Y}📤 Sending...{W}", end=" ")
                if self.send_offer_email(candidate, {'role': m_role, 'start_date': sheet_start}):
                    try:
                        headers = self.worksheet.row_values(1)
                        status_col = next(i for i, h in enumerate(headers, 1) if "status" in str(h).lower())
                        self.worksheet.update_cell(candidate['_row'], status_col, "Internship Ongoing")
                        print(f"{G}✅ Sent! Status -> 'Internship Ongoing'{W}")
                    except:
                        print(f"{G}✅ Sent! (Status update failed){W}")
                else:
                    print(f"{R}❌ Failed.{W}")
            
            elif choice == '2': continue
            elif choice == '3': return

def main():
    OfferEmailSender().run_process()

if __name__ == "__main__":
    main()