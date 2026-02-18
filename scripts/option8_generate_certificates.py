import os
import re
import gspread
import time
import pickle # Added for Drive Auth
import win32com.client
from docx import Document
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from lxml import etree

# --- Google Drive API Imports ---
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ANSI Colors
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class CertificateGenerator:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))
        
        # --- Credentials & Config ---
        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        self.client_secret_file = os.path.join(self.script_dir, "client_secret.json") 
        self.token_file = os.path.join(self.script_dir, "token.json") 
        
        self.sheet_url = str(os.getenv("REGISTRATION_SHEET_URL", "")).strip()
        self.drive_folder_id = os.getenv("CERTIFICATES_DRIVE_FOLDER_ID") # Uses the specific Cert Folder ID
        
        self.template_path = os.path.join(self.script_dir, "templates", "Completion_Certificate.docx")
        self.output_dir = os.path.join(self.script_dir, "output", "certificates")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.sheet_instance = None
        self.drive_service = None

    # --- DRIVE AUTHENTICATION ---
    def get_drive_service(self):
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    if os.path.exists(self.token_file): os.remove(self.token_file)
                    return self.get_drive_service()
            else:
                if not os.path.exists(self.client_secret_file):
                    print(f"{R}❌ Error: 'client_secret.json' missing.{W}")
                    return None
                
                print(f"{Y}🔓 Opening browser for Google Login...{W}")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, ['https://www.googleapis.com/auth/drive.file']
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        return build('drive', 'v3', credentials=creds)

    def connect(self):
        print(f"{Y}⏳ Connecting to Google Services...{W}")
        if not os.path.exists(self.creds_file):
            print(f"{R}❌ Error: 'service_account.json' missing.{W}"); return False

        try:
            # 1. Connect Sheets
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            
            # 2. Connect Drive
            self.drive_service = self.get_drive_service()

            if not self.sheet_url:
                print(f"{R}❌ Error: REGISTRATION_SHEET_URL missing in .env{W}"); return False

            spreadsheet = client.open_by_url(self.sheet_url)
            gid_match = re.search(r'gid=([0-9]+)', self.sheet_url)
            
            target_sheet = None
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        target_sheet = sheet; break
            
            self.sheet_instance = target_sheet if target_sheet else spreadsheet.get_worksheet(0)
            print(f"{G}✅ Connected to Tab: {self.sheet_instance.title}{W}")
            return True
        except Exception as e:
            print(f"{R}❌ Connection Failed: {e}{W}"); return False

    def upload_to_drive(self, file_path, file_name):
        if not self.drive_service:
            print(f"{Y}⚠️  Drive Service not connected.{W}")
            return
        
        if not self.drive_folder_id:
            print(f"{Y}⚠️  CERTIFICATES_DRIVE_FOLDER_ID is missing in .env!{W}")
            return

        try:
            print(f"{Y}☁️  Uploading to Google Drive...{W}", end=" ")
            file_metadata = {'name': file_name, 'parents': [self.drive_folder_id]}
            media = MediaFileUpload(file_path, mimetype='application/pdf')
            file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"{G}Done! (File ID: {file.get('id')}){W}")
            return file.get('id')
        except Exception as e:
            print(f"\n{R}❌ Drive Upload Failed: {e}{W}")

    def update_status(self, row_idx, status_text):
        try:
            headers = self.sheet_instance.row_values(1)
            col_idx = next((i for i, h in enumerate(headers, 1) if "status" in str(h).lower()), None)
            if col_idx:
                self.sheet_instance.update_cell(row_idx, col_idx, status_text)
                return True
            return False
        except: return False

    def update_sheet_dates(self, row_idx, start_date, end_date):
        """Updates the Start and End date columns in the sheet if they changed"""
        try:
            headers = self.sheet_instance.row_values(1)
            
            start_col = next((i for i, h in enumerate(headers, 1) 
                              if any(x in str(h).lower() for x in ["start_date", "start date", "joining date"])), None)
            
            end_col = next((i for i, h in enumerate(headers, 1) 
                            if any(x in str(h).lower() for x in ["end_date", "end date", "completion date"])), None)

            if start_col and start_date:
                self.sheet_instance.update_cell(row_idx, start_col, start_date)
            
            if end_col and end_date:
                self.sheet_instance.update_cell(row_idx, end_col, end_date)
                
            return True
        except Exception as e:
            print(f"{R}   ⚠️  Failed to update dates in sheet: {e}{W}")
            return False

    def clean_xml_tags(self, xml_str):
        xml_str = re.sub(r'<w:proofErr[^>]*>', '', xml_str)
        xml_str = re.sub(r'<w:gramE[^>]*>', '', xml_str)
        xml_str = re.sub(r'<w:lang[^>]*>', '', xml_str)
        return xml_str

    def nuclear_replace(self, doc, data):
        xml_body = doc.element.body
        xml_str = xml_body.xml
        xml_str = self.clean_xml_tags(xml_str)
        original_xml = xml_str
        
        for key, val in data.items():
            safe_val = str(val).replace("<", "&lt;").replace(">", "&gt;")
            if key in xml_str:
                xml_str = xml_str.replace(key, safe_val)
        
        if xml_str != original_xml:
            new_body = etree.fromstring(xml_str)
            doc.element.replace(xml_body, new_body)

    def convert_to_pdf(self, docx_path, pdf_path):
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(docx_path)
            doc.SaveAs(pdf_path, FileFormat=17)
            doc.Close()
            word.Quit()
            if os.path.exists(docx_path): os.remove(docx_path)
            return True
        except Exception as e: 
            return False

    def get_val(self, student, keys):
        for k in keys:
            for d_k in student.keys():
                if k.lower() == d_k.lower(): return str(student[d_k]).strip()
        return ""

    def generate_docx(self, student, dates, common_data):
        first_name = self.get_val(student, ["First Name", "First_Name", "Name", "Student Name"])
        last_name  = self.get_val(student, ["Last Name", "Last_Name", "Surname"])
        full_name = f"{first_name} {last_name}".strip() if first_name else "Student"
        
        replacements = {
            "{FULL_NAME}": full_name,
            "{FROM}": dates['start'],
            "{TO}": dates['end'],
            "{ROLE}": common_data['role'],
            "{CURRENT_DATE}": common_data['issue_date']
        }

        doc = Document(self.template_path)
        self.nuclear_replace(doc, replacements)
        
        safe_name = "".join([c if c.isalnum() else "_" for c in first_name])
        filename_base = f"Cert_{safe_name}"
        
        docx_path = os.path.abspath(os.path.join(self.output_dir, f"{filename_base}.docx"))
        pdf_path = os.path.abspath(os.path.join(self.output_dir, f"{filename_base}.pdf"))
        
        # Retry logic for open files
        while True:
            try:
                doc.save(docx_path)
                break
            except PermissionError:
                print(f"\n{R}❌ ERROR: The file '{filename_base}.docx' is OPEN! Close it and press Enter.{W}")
                input()
            except Exception as e:
                print(f"{R}❌ Save Failed: {e}{W}")
                return None, None

        return docx_path, pdf_path

    def run(self):
        if not self.connect(): return

        print(f"\n{B}🎓 --- Internship Certificate Generator (Interactive) ---{W}")
        today = datetime.now().strftime("%B %d, %Y")
        
        issue_date = input(f"📅 Issue Date [{today}]: ").strip() or today
        role = input(f"💼 Role [Software Developer - Intern]: ").strip() or "Software Developer - Intern"
        common_data = {'issue_date': issue_date, 'role': role}

        students = self.sheet_instance.get_all_records()
        
        ongoing_interns = []
        for i, s in enumerate(students):
            if "internship ongoing" in str(s.get("Status", "")).lower():
                ongoing_interns.append((i+2, s))

        if not ongoing_interns:
            print(f"{G}✅ No 'Internship Ongoing' candidates found.{W}"); return

        print(f"\n{Y}🔍 Found {len(ongoing_interns)} candidates.{W}")

        for idx, (row_num, student) in enumerate(ongoing_interns, 1):
            name = self.get_val(student, ["First Name", "Name"]) or "Candidate"
            sheet_start = self.get_val(student, ["Start_Date", "Start Date", "Joining Date"])
            sheet_end = self.get_val(student, ["End_Date", "End Date", "Completion Date"])
            
            print(f"\n{C}{'-'*60}{W}")
            print(f"👤 Candidate [{idx}/{len(ongoing_interns)}]: {B}{name}{W}")
            
            # --- START DATE ---
            final_start = sheet_start
            if sheet_start:
                choice = input(f"   👉 Use Start Date (Sheet: {Y}{sheet_start}{W})? [y/n]: ").strip().lower()
                if choice != 'y': final_start = input(f"   ✍️  Enter Start Date: ").strip()
            else:
                final_start = input(f"   ✍️  Enter Start Date: ").strip()

            # --- END DATE ---
            final_end = sheet_end
            if sheet_end:
                choice = input(f"   👉 Use End Date   (Sheet: {Y}{sheet_end}{W})? [y/n]: ").strip().lower()
                if choice != 'y': final_end = input(f"   ✍️  Enter End Date:   ").strip()
            else:
                final_end = input(f"   ✍️  Enter End Date:   ").strip()

            if not final_start or not final_end:
                print(f"{R}❌ Skipping (Missing Dates){W}"); continue

            # --- UPDATE SHEET IF DATES CHANGED ---
            if final_start != sheet_start or final_end != sheet_end:
                print(f"{Y}   📝 Updating dates in sheet...{W}", end=" ")
                if self.update_sheet_dates(row_num, final_start, final_end):
                    print(f"{G}Done!{W}")

            # --- GENERATE ---
            print(f"{Y}⚙️  Generating...{W}", end=" ")
            docx, pdf = self.generate_docx(student, {'start': final_start, 'end': final_end}, common_data)
            
            if docx and pdf:
                if self.convert_to_pdf(docx, pdf):
                    print(f"{G}✅ Done!{W}")
                    
                    # --- DRIVE UPLOAD ---
                    if os.path.exists(pdf):
                        self.upload_to_drive(pdf, os.path.basename(pdf))
                    # --------------------

                    # Update status to 'Certificate Generated'
                    if self.update_status(row_num, "Certificate Generated"):
                        print(f"   📝 Status Updated -> 'Certificate Generated'")
                else:
                    print(f"{R}❌ Conversion Failed.{W}")

        print(f"\n{G}✨ All Done! Check 'output/certificates' folder.{W}")
        try: os.startfile(self.output_dir)
        except: pass

def main():
    CertificateGenerator().run()

if __name__ == "__main__":
    main()