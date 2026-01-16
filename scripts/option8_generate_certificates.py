import os
import gspread
from docx import Document
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import win32com.client
import pythoncom
from lxml import etree

# ANSI colors
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class CertificateGenerator:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))
        
        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        self.sheet_url = os.getenv("OFFER_DETAILS_SHEET_URL") 
        self.template_docx = os.path.join(self.script_dir, "templates", "Completion_Certificate.docx")
        self.output_dir = os.path.join(self.script_dir, "output", "certificates")
        os.makedirs(self.output_dir, exist_ok=True)

    def connect_to_sheet(self):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            return client.open_by_url(self.sheet_url).get_worksheet(0)
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}")
            return None

    def replace_placeholders(self, doc, data):
        """Replace placeholders EVERYWHERE in the document using multiple methods"""
        
        print(f"{Y}🔍 Searching for placeholders...{W}")
        
        # Method 1: Regular paragraphs
        count = 0
        for paragraph in doc.paragraphs:
            if self._contains_placeholder(paragraph.text, data):
                self._replace_in_paragraph(paragraph, data)
                count += 1
        print(f"   Found {count} in paragraphs")
        
        # Method 2: Tables
        count = 0
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if self._contains_placeholder(paragraph.text, data):
                            self._replace_in_paragraph(paragraph, data)
                            count += 1
        print(f"   Found {count} in tables")
        
        # Method 3: Direct XML replacement (catches text boxes)
        count = self._replace_in_xml(doc, data)
        print(f"   Found {count} in XML elements (including text boxes)")

    def _replace_in_xml(self, doc, data):
        """Aggressively replace in ALL XML text nodes"""
        count = 0
        
        # Get the document XML tree
        tree = doc.element
        
        # Define namespaces
        namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
        }
        
        # Find ALL text elements (w:t tags)
        for t_elem in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if t_elem.text:
                original = t_elem.text
                new_text = original
                
                for key, value in data.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in new_text:
                        new_text = new_text.replace(placeholder, str(value))
                        count += 1
                
                if new_text != original:
                    t_elem.text = new_text
        
        # Also check DrawingML text (a:t tags) - sometimes used in text boxes
        for t_elem in tree.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t'):
            if t_elem.text:
                original = t_elem.text
                new_text = original
                
                for key, value in data.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in new_text:
                        new_text = new_text.replace(placeholder, str(value))
                        count += 1
                
                if new_text != original:
                    t_elem.text = new_text
        
        return count

    def _contains_placeholder(self, text, data):
        return any(f"{{{key}}}" in text for key in data.keys())

    def _replace_in_paragraph(self, paragraph, data):
        """Replace text in paragraph while preserving formatting"""
        original_text = paragraph.text
        new_text = original_text
        
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in new_text:
                new_text = new_text.replace(placeholder, str(value))
        
        if new_text == original_text:
            return
        
        if paragraph.runs:
            first_run = paragraph.runs[0]
            font_props = {
                'name': first_run.font.name,
                'size': first_run.font.size,
                'bold': first_run.font.bold,
                'italic': first_run.font.italic,
                'underline': first_run.font.underline,
                'color': first_run.font.color.rgb if first_run.font.color else None
            }
            
            # Remove all runs
            for _ in range(len(paragraph.runs)):
                paragraph._element.remove(paragraph.runs[0]._element)
            
            # Add new run with replaced text
            new_run = paragraph.add_run(new_text)
            
            # Apply formatting
            new_run.font.name = font_props['name']
            new_run.font.size = font_props['size']
            new_run.font.bold = font_props['bold']
            new_run.font.italic = font_props['italic']
            new_run.font.underline = font_props['underline']
            if font_props['color']:
                new_run.font.color.rgb = font_props['color']

    def generate_certificate_pdf(self, candidate, manual_data):
        full_name = (candidate.get("Full Name(as per Aadhar/PAN)") or "Candidate").strip()
        
        # Data dictionary with all placeholders
        data = {
            "FULL_NAME": full_name,
            "FROM": manual_data['start_date'],
            "TO": manual_data['end_date'],
            "CURRENT_DATE": manual_data['issue_date'],
            "ROLE": manual_data['role']
        }

        print(f"\n{C}📋 Data to replace:{W}")
        for key, value in data.items():
            print(f"   {{{key}}} → {value}")

        # 1. Load template and replace placeholders
        doc = Document(self.template_docx)
        self.replace_placeholders(doc, data)

        # 2. Create safe filename
        safe_name = "".join([c if c.isalnum() or c == '_' else "_" for c in full_name])
        
        # Win32com requires ABSOLUTE paths
        docx_path = os.path.abspath(os.path.join(self.output_dir, f"Cert_{safe_name}.docx"))
        pdf_path = os.path.abspath(os.path.join(self.output_dir, f"Cert_{safe_name}.pdf"))

        # 3. Save DOCX
        doc.save(docx_path)
        print(f"{G}✅ DOCX saved: {docx_path}{W}")
        
        # 4. Convert to PDF using Word COM
        try:
            pythoncom.CoInitialize()
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            
            # Open the DOCX
            wb = word.Documents.Open(docx_path)
            
            # Save as PDF (FileFormat=17)
            wb.SaveAs(pdf_path, FileFormat=17)
            wb.Close()
            word.Quit()
            
            # Cleanup - remove DOCX, keep PDF
            if os.path.exists(pdf_path):
                print(f"{G}✅ PDF created: {pdf_path}{W}")
                os.remove(docx_path) 
                return pdf_path
            return docx_path
            
        except Exception as e:
            print(f"{R}❌ PDF Error: {e}{W}")
            try: 
                word.Quit() 
            except: 
                pass
            return docx_path

    def run_process(self):
        sheet = self.connect_to_sheet()
        if not sheet: 
            return
            
        print(f"{Y}⏳ Fetching candidates from sheet...{W}")
        candidates = sheet.get_all_records()

        for idx, candidate in enumerate(candidates, 1):
            name = (candidate.get("Full Name(as per Aadhar/PAN)") or "Unknown")
            
            print(f"\n{B}{'='*60}{W}")
            print(f"{B}[{idx}/{len(candidates)}] {name}{W}")
            print(f"{B}{'='*60}{W}")
            
            choice = input(f"Generate Certificate? (y/n/exit): ").strip().lower()
            
            if choice == "exit": 
                break
            if choice != "y": 
                continue
            
            today = datetime.now().strftime("%d-%m-%Y")
            sheet_start = candidate.get("Expected Start Date") or candidate.get("Start Date") or ""
            
            # Get manual inputs
            m_start = input(f"🗓️  Start Date [{sheet_start}]: ").strip() or str(sheet_start)
            m_end = input(f"🏁 End Date [{today}]: ").strip() or today
            m_issue = input(f"📅 Issue Date [{today}]: ").strip() or today
            m_role = input(f"💼 Role [MERN Stack]: ").strip() or "MERN Stack"

            manual_inputs = {
                'start_date': m_start,
                'end_date': m_end,
                'issue_date': m_issue,
                'role': m_role
            }

            try:
                print(f"\n{Y}⚙️  Generating certificate...{W}")
                output_path = self.generate_certificate_pdf(candidate, manual_inputs)
                print(f"\n{G}{'='*60}{W}")
                print(f"{G}✅ SUCCESS! Certificate generated:{W}")
                print(f"{G}   {output_path}{W}")
                print(f"{G}{'='*60}{W}\n")
                
            except Exception as e:
                print(f"\n{R}{'='*60}{W}")
                print(f"{R}❌ FAILED: {e}{W}")
                print(f"{R}{'='*60}{W}\n")
                import traceback
                traceback.print_exc()

def main():
    print(f"{B}{'='*60}{W}")
    print(f"{B}🎓 SwipeGen Certificate Generator{W}")
    print(f"{B}{'='*60}{W}\n")
    generator = CertificateGenerator()
    generator.run_process()
    print(f"\n{G}✨ Done!{W}")
    input(f"{C}Press Enter to exit...{W}")

if __name__ == "__main__":
    main()