import os
import re
import gspread
import pickle
from docx import Document
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import win32com.client
import pythoncom

# Google Drive API Imports (User OAuth)
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class CertificateGenerator:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))
        
        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        self.client_secret_file = os.path.join(self.script_dir, "client_secret.json") # REQUIRED for Drive
        self.token_file = os.path.join(self.script_dir, "token.json") 
        
        self.sheet_url = os.getenv("OFFER_DETAILS_SHEET_URL") 
        self.drive_folder_id = os.getenv("CERTIFICATES_DRIVE_FOLDER_ID")
        
        self.template_docx = os.path.join(self.script_dir, "templates", "Completion_Certificate.docx")
        self.output_dir = os.path.join(self.script_dir, "output", "certificates")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.drive_service = None 

    def get_drive_service(self):
        """Authenticates as YOU (User) to use your personal storage quota"""
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
                    print(f"{R}❌ Error: 'client_secret.json' missing in scripts folder.{W}")
                    return None
                
                print(f"{Y}🔓 Opening browser for Google Login...{W}")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, ['https://www.googleapis.com/auth/drive.file']
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        return build('drive', 'v3', credentials=creds)

    def connect_services(self):
        try:
            # 1. Sheets (Service Account)
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            
            # 2. Drive (User OAuth)
            self.drive_service = self.get_drive_service()

            spreadsheet = client.open_by_url(self.sheet_url)
            gid_match = re.search(r'gid=([0-9]+)', self.sheet_url)
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        return sheet
            return spreadsheet.get_worksheet(0)
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}")
            return None

    def upload_to_drive(self, file_path, file_name):
        if not self.drive_service:
            print(f"{Y}⚠️  Drive Login failed. Skipping upload.{W}")
            return
            
        if not self.drive_folder_id:
            print(f"{Y}⚠️  CERTIFICATES_DRIVE_FOLDER_ID missing in .env.{W}")
            return

        try:
            print(f"{Y}☁️  Uploading to Google Drive (User Storage)...{W}", end=" ")
            file_metadata = {'name': file_name, 'parents': [self.drive_folder_id]}
            media = MediaFileUpload(file_path, mimetype='application/pdf')
            file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"{G}Done! (File ID: {file.get('id')}){W}")
            return file.get('id')
        except Exception as e:
            print(f"\n{R}❌ Drive Upload Failed: {e}{W}")

    def replace_placeholders(self, doc, data):
        print(f"{Y}🔍 Searching for placeholders...{W}")
        count = 0
        for paragraph in doc.paragraphs:
            if self._contains_placeholder(paragraph.text, data):
                self._replace_in_paragraph(paragraph, data); count += 1
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if self._contains_placeholder(paragraph.text, data):
                            self._replace_in_paragraph(paragraph, data); count += 1
        count += self._replace_in_xml(doc, data)
        print(f"   Found/Replaced occurrences.")

    def _replace_in_xml(self, doc, data):
        tree = doc.element
        for t_elem in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if t_elem.text:
                new_text = t_elem.text
                for k, v in data.items(): new_text = new_text.replace(f"{{{k}}}", str(v))
                if new_text != t_elem.text: t_elem.text = new_text
        for t_elem in tree.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
            if t_elem.text:
                new_text = t_elem.text
                for k, v in data.items(): new_text = new_text.replace(f"{{{k}}}", str(v))
                if new_text != t_elem.text: t_elem.text = new_text
        return 0

    def _contains_placeholder(self, text, data):
        return any(f"{{{key}}}" in text for key in data.keys())

    def _replace_in_paragraph(self, paragraph, data):
        original = paragraph.text
        new_text = original
        for k, v in data.items(): new_text = new_text.replace(f"{{{k}}}", str(v))
        if new_text == original: return
        if paragraph.runs:
            r = paragraph.runs[0]
            font_props = {'name': r.font.name, 'size': r.font.size, 'bold': r.font.bold, 'italic': r.font.italic, 'underline': r.font.underline, 'color': r.font.color.rgb if r.font.color else None}
            for _ in range(len(paragraph.runs)): paragraph._element.remove(paragraph.runs[0]._element)
            new_run = paragraph.add_run(new_text)
            new_run.font.name = font_props['name']; new_run.font.size = font_props['size']; new_run.font.bold = font_props['bold']; new_run.font.italic = font_props['italic']; new_run.font.underline = font_props['underline']
            if font_props['color']: new_run.font.color.rgb = font_props['color']

    def generate_certificate_pdf(self, candidate, manual_data):
        full_name = (candidate.get("Full Name(as per Aadhar/PAN)") or "Candidate").strip()
        data = {
            "FULL_NAME": full_name, "FROM": manual_data['start_date'],
            "TO": manual_data['end_date'], "CURRENT_DATE": manual_data['issue_date'],
            "ROLE": manual_data['role']
        }
        
        doc = Document(self.template_docx)
        self.replace_placeholders(doc, data)
        
        safe_name = "".join([c if c.isalnum() or c == '_' else "_" for c in full_name])
        pdf_filename = f"Cert_{safe_name}.pdf"
        
        docx_path = os.path.abspath(os.path.join(self.output_dir, f"Cert_{safe_name}.docx"))
        pdf_path = os.path.abspath(os.path.join(self.output_dir, pdf_filename))
        
        doc.save(docx_path)
        
        try:
            pythoncom.CoInitialize()
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            wb = word.Documents.Open(docx_path)
            wb.SaveAs(pdf_path, FileFormat=17)
            wb.Close(); word.Quit()
            
            if os.path.exists(pdf_path):
                os.remove(docx_path)
                return pdf_path, pdf_filename
            return docx_path, None
        except Exception as e:
            print(f"{R}❌ PDF Error: {e}{W}")
            try: word.Quit()
            except: pass
            return docx_path, None

    def run_process(self):
        sheet = self.connect_services()
        if not sheet: return
        
        print(f"{Y}⏳ Fetching candidates...{W}")
        candidates = sheet.get_all_records()
        
        for idx, candidate in enumerate(candidates, 1):
            name = (candidate.get("Full Name(as per Aadhar/PAN)") or "Unknown")
            print(f"\n{B}[{idx}/{len(candidates)}] {name}{W}")
            
            choice = input(f"Generate? (y/n/exit): ").strip().lower()
            if choice == "exit": break
            if choice != "y": continue
            
            today = datetime.now().strftime("%d-%m-%Y")
            sheet_start = candidate.get("Expected Start Date") or candidate.get("Start Date") or ""
            m_start = input(f"🗓️  Start Date [{sheet_start}]: ").strip() or str(sheet_start)
            m_end = input(f"🏁 End Date [{today}]: ").strip() or today
            m_issue = input(f"📅 Issue Date [{today}]: ").strip() or today
            m_role = input(f"💼 Role [MERN Stack]: ").strip() or "MERN Stack"

            try:
                print(f"\n{Y}⚙️  Generating local file...{W}")
                output_path, file_name = self.generate_certificate_pdf(
                    candidate, 
                    {'start_date': m_start, 'end_date': m_end, 'issue_date': m_issue, 'role': m_role}
                )
                print(f"{G}✅ Local PDF saved: {output_path}{W}")
                
                if output_path and file_name and output_path.endswith('.pdf'):
                    self.upload_to_drive(output_path, file_name)

            except Exception as e:
                print(f"{R}❌ FAILED: {e}{W}")

def main():
    print(f"{B}🎓 SwipeGen Certificate Generator (Local + User Drive Backup){W}\n")
    generator = CertificateGenerator()
    generator.run_process()
    print(f"\n{G}✨ Done!{W}")

if __name__ == "__main__":
    main()