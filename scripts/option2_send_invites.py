import os
import re
import smtplib
import gspread
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage  # Required for local images
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class InterviewInviter:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.base_dir, '..', '.env'))
        
        self.creds_file = os.path.join(self.base_dir, "service_account.json")
        self.images_dir = os.path.join(self.base_dir, "images")  # Local images folder
        
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.google_form_url = "https://forms.gle/zivKMBVxaRLrPhDGA"
        self.worksheet = None

        # 1. Map Template Placeholders to Local Filenames
        self.local_images = {
            "logo_url": "logo.png",
            "ig_icon": "instagram.png",
            "li_icon": "linkedin.png",
            "google_icon": "google.png"
        }

        # 2. Data for HTML Replacement
        # Notice we use "cid:placeholder_name" instead of a URL
        self.social_links = {
            "web_link": os.getenv("WEBSITE_URL", "#"),
            "ig_link": os.getenv("INSTAGRAM_URL", "#"),
            "li_link": os.getenv("LINKEDIN_URL", "#"),
            "google_link": os.getenv("GOOGLE_SEARCH_URL", "#"),
            
            # These point to the Content-IDs we will attach later
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
            
            if not self.sheet_url:
                print(f"{R}❌ REGISTRATION_SHEET_URL missing in .env{W}"); return False

            spreadsheet = client.open_by_url(self.sheet_url)

            # Smart Tab Finder
            gid_match = re.search(r'gid=([0-9]+)', self.sheet_url)
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        self.worksheet = sheet
                        print(f"{G}✅ Connected to tab: {sheet.title}{W}")
                        return True
            
            self.worksheet = spreadsheet.get_worksheet(0)
            print(f"{Y}⚠️ Using first tab: {self.worksheet.title}{W}")
            return True
        except Exception as e:
            print(f"{R}Connection Error: {e}{W}")
            return False

    def _get_template(self, name):
        """Reads HTML template and fills in data"""
        try:
            template_path = os.path.join(self.base_dir, "templates", "interview_email_template.html")
            with open(template_path, "r", encoding="utf-8") as file:
                tpl = file.read()
                # Fill placeholders with name, form link, and cid references
                return tpl.format(name=name, form_url=self.google_form_url, **self.social_links)
        except Exception as e:
            print(f"{R}❌ Template Error: {e}{W}")
            return f"<p>Hi {name}, please confirm your interview here: <a href='{self.google_form_url}'>Link</a></p>"

    def fetch_by_status(self, status_text):
        try:
            all_records = self.worksheet.get_all_records()
            return [dict(row, _row=i+2) for i, row in enumerate(all_records) if str(row.get('Status', '')).strip() == status_text]
        except Exception as e:
            print(f"{R}❌ Fetch Error: {e}{W}"); return []

    def display_candidates(self, candidates, title):
        print(f"\n{C}{'='*105}\n {title} ({len(candidates)})\n{'='*105}{W}")
        print(f"{ 'SL No.':<8} | {'Name':<15} | {'Email':<30} | {'Resume Link'}")
        print("-" * 105)
        for i, c in enumerate(candidates, 1):
            name = c.get('First Name') or c.get('Name') or "N/A"
            email = c.get('Email address') or c.get('Email') or "N/A"
            resume = c.get('Resume Link') or c.get('Resume') or "N/A"
            print(f"{i:<8} | {name:<15} | {email:<30} | {C}{resume}{W}")
        print("-" * 105)

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
            # Define the Content-ID so HTML can find it (<img src="cid:logo_url">)
            image.add_header('Content-ID', f'<{content_id}>') 
            image.add_header('Content-Disposition', 'inline', filename=filename)
            msg.attach(image)
        except Exception as e:
            print(f"{R}   ❌ Failed to attach {filename}: {e}{W}")

    def send_bulk_emails(self, candidates):
        if not self.sender_email or not self.sender_password:
            print(f"{R}❌ Credentials missing in .env!{W}"); return
            
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            # Find Status Column Index
            headers = self.worksheet.row_values(1)
            status_col = next((i for i, h in enumerate(headers, 1) if "status" in str(h).lower()), 1)

            print(f"\n{Y}🚀 Starting email broadcast...{W}")
            
            for c in candidates:
                name = c.get('First Name') or c.get('Name') or "Candidate"
                email = c.get('Email address') or c.get('Email')
                
                if not email: 
                    print(f"{R}Skipping row {c['_row']} (No Email){W}")
                    continue

                # 1. Create 'Related' container (Required for inline images)
                msg = MIMEMultipart('related')
                msg['From'] = self.sender_email
                msg['To'] = email
                msg['Subject'] = "HR-Automation - Interview Confirmation"

                # 2. Attach HTML Body
                html_content = self._get_template(name)
                msg_html = MIMEText(html_content, 'html')
                msg.attach(msg_html)

                # 3. Attach Local Images
                # Loops through self.local_images to attach logo.png, instagram.png, etc.
                for cid_name, filename in self.local_images.items():
                    self.attach_image(msg, filename, cid_name)

                # 4. Send
                try:
                    server.sendmail(self.sender_email, email, msg.as_string())
                    self.worksheet.update_cell(c['_row'], status_col, "Invited for Interview")
                    print(f"{G}✅ Sent: {email}{W}")
                except Exception as e:
                    print(f"{R}❌ Failed: {email} - {e}{W}")
                
                time.sleep(1) # Prevent spam blocking

            server.quit()
            print(f"\n{G}✨ Broadcast Complete!{W}")

        except Exception as e:
            print(f"{R}❌ SMTP Connection Error: {e}{W}")

def main():
    inviter = InterviewInviter()
    if not inviter.connect(): return
    
    while True:
        print(f"\n{B}--- HR-AUTOMATION INTERVIEW INVITER (Local Images) ---{W}")
        print(f"1. Send Invites (Shortlisted)")
        print(f"2. View Rejected")
        print(f"3. Exit")
        
        choice = input(f"\n👉 {C}Select option: {W}").strip()
        
        if choice == '1':
            candidates = inviter.fetch_by_status("Resume Shortlisted")
            if not candidates: 
                print(f"{R}❌ No 'Resume Shortlisted' candidates found.{W}")
                continue
                
            inviter.display_candidates(candidates, "SHORTLISTED CANDIDATES")
            
            action = input(f"\n👉 {C}Type 'all' or range '1-5': {W}").strip().lower()
            if action == 'all':
                inviter.send_bulk_emails(candidates)
            elif '-' in action:
                try:
                    s, e = map(int, action.split('-'))
                    inviter.send_bulk_emails(candidates[s-1:e])
                except: print(f"{R}❌ Invalid range.{W}")
        
        elif choice == '2':
            candidates = inviter.fetch_by_status("Not Shortlisted")
            inviter.display_candidates(candidates, "REJECTED CANDIDATES")
            
        elif choice == '3': 
            break

if __name__ == "__main__":
    main()