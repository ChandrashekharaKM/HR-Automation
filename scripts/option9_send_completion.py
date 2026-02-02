import os
import time
import re
import gspread
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class CompletionEmailSender:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))
        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.template_path = os.path.join(self.script_dir, "templates", "completion_email_template.html")
        self.cert_folder = os.path.join(self.script_dir, "output", "certificates")
        self.social_links = {
            "ig_link": "https://www.instagram.com/swipegen/",
            "li_link": "https://www.linkedin.com/company/swipegen",
            "web_link": "https://www.swipegen.in"
        }

    def connect_sheet(self):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_url(self.sheet_url)
            
            # SMART FIX: Check for GID
            gid_match = re.search(r'gid=([0-9]+)', self.sheet_url)
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        return sheet
            
            # Fallback
            return spreadsheet.get_worksheet(0)
        except Exception as e:
            print(f"{R}❌ Sheet Connection Error: {e}{W}")
            return None

    def _get_email_from_record(self, record):
        possible_keys = ['Email', 'Email Address', 'Email ID', 'Personal Email', 'Official Email', 'Student Email', 'Candidate Email']
        for key in possible_keys:
            if record.get(key): return str(record.get(key)).strip()
        for record_key in record.keys():
            if record_key.strip().lower() in [k.lower() for k in possible_keys] and record.get(record_key):
                return str(record.get(record_key)).strip()
        return None

    def get_ongoing_interns(self, sheet):
        try:
            all_records = sheet.get_all_records()
            ongoing = []
            for i, record in enumerate(all_records, start=2):
                status = str(record.get('Status', '')).strip()
                if status.lower() == "internship ongoing":
                    record['row_num'] = i 
                    record['final_email'] = self._get_email_from_record(record)
                    ongoing.append(record)
            return ongoing
        except Exception as e:
            print(f"{R}❌ Error fetching records: {e}{W}")
            return []

    def get_certificate_path(self, full_name):
        clean_name = str(full_name).strip()
        safe_name = "".join([c if c.isalnum() or c == '_' else "_" for c in clean_name])
        filename = f"Cert_{safe_name}.pdf"
        return os.path.join(self.cert_folder, filename), filename

    def send_email(self, candidate):
        raw_name = candidate.get('Full Name(as per Aadhar/PAN)') or candidate.get('Name') or "Candidate"
        name = str(raw_name).strip()
        to_email = candidate.get('final_email')
        
        if not to_email:
            print(f"{R}   ⚠️  Skipping: No email found for {name}{W}")
            return False

        cert_path, cert_filename = self.get_certificate_path(name)
        if not os.path.exists(cert_path):
            print(f"{R}   ❌ Missing Certificate: {cert_filename}{W}")
            print(f"{Y}      (Please check output/certificates folder or run Option 8){W}")
            return False

        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                body_html = f.read()
            
            body_html = body_html.replace("{name}", name)
            for key, value in self.social_links.items():
                body_html = body_html.replace(f"{{{key}}}", value)

            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = "Congratulations on your Completion! - SwipeGen"
            msg.attach(MIMEText(body_html, 'html'))

            with open(cert_path, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header('Content-Disposition', 'attachment', filename=cert_filename)
                msg.attach(attach)

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"{R}   ❌ Email Failed for {name}: {e}{W}")
            return False

    def update_status(self, sheet, row_num):
        try:
            headers = sheet.row_values(1)
            try:
                col_index = headers.index("Status") + 1
            except ValueError:
                print(f"{R}   ❌ 'Status' column not found.{W}")
                return False
            sheet.update_cell(row_num, col_index, "Internship Completed")
            return True
        except Exception as e:
            print(f"{R}   ❌ Status Update Failed (Row {row_num}): {e}{W}")
            return False

    def run(self):
        print(f"\n{B}📧 SwipeGen Completion Email Automation{W}")
        print(f"{C}{'='*40}{W}")
        sheet = self.connect_sheet()
        if not sheet: return

        print(f"{Y}⏳ Fetching 'Internship Ongoing' candidates...{W}")
        candidates = self.get_ongoing_interns(sheet)

        if not candidates:
            print(f"{G}✨ No ongoing internships found.{W}")
            return

        print(f"\n{G}found {len(candidates)} active interns:{W}")
        print(f"{'No.':<5} {'Name':<30} {'Certificate Status':<30}")
        print("-" * 65)
        
        for idx, c in enumerate(candidates, 1):
            raw_name = c.get('Full Name(as per Aadhar/PAN)') or c.get('Name') or "Unknown"
            name = str(raw_name).strip()
            cert_path, _ = self.get_certificate_path(name)
            cert_status = f"{G}Found{W}" if os.path.exists(cert_path) else f"{R}Missing{W}"
            print(f"{idx:<5} {name[:28]:<30} {cert_status:<30}")

        print("-" * 65)
        print(f"\n{Y}Options:{W}")
        print("1. Update ALL candidates (Only those with certificates)")
        print("2. Update SELECTED candidates")
        print("3. Exit")
        
        choice = input(f"\n👉 {B}Enter choice: {W}").strip()
        targets = []
        if choice == '1':
            targets = candidates
        elif choice == '2':
            selection = input(f"👉 Enter numbers (comma separated): ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip().isdigit()]
                for i in indices:
                    if 0 <= i < len(candidates):
                        targets.append(candidates[i])
            except:
                print(f"{R}❌ Invalid selection.{W}")
                return
        else:
            return

        print(f"\n{Y}🚀 Processing {len(targets)} candidates...{W}\n")
        success_count = 0
        for person in targets:
            raw_name = person.get('Full Name(as per Aadhar/PAN)') or person.get('Name')
            name = str(raw_name).strip()
            print(f"{C}Processing: {name}...{W}", end=" ")
            
            if self.send_email(person):
                print(f"{G}[Email Sent + Cert Attached]{W}", end=" ")
                if self.update_status(sheet, person['row_num']):
                    print(f"{G}[Status Updated]{W}")
                    success_count += 1
                else:
                    print(f"{R}[Status Failed]{W}")
            else:
                print(f"{R}[Failed]{W}")
            time.sleep(1.5)

        print(f"\n{G}✨ Done! {success_count}/{len(targets)} processed.{W}")
        input(f"{C}Press Enter to exit...{W}")

# ✅ Added main wrapper function
def main():
    try:
        sender = CompletionEmailSender()
        sender.run()
    except Exception as e:
        print(f"{R}Unexpected Error in Option 9: {e}{W}")

if __name__ == "__main__":
    main()