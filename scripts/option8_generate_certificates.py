import os
import gspread
from docx import Document
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import win32com.client
import pythoncom
from lxml import etree

# Define ANSI colors for terminal output (Green, Red, Yellow, Blue, Cyan, White)
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class CertificateGenerator:
    def __init__(self):
        # Set the base directory to the current script's location
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load environment variables from the parent directory
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))
        
        # Define paths for credentials, template, and output folders
        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        self.sheet_url = os.getenv("OFFER_DETAILS_SHEET_URL") 
        self.template_docx = os.path.join(self.script_dir, "templates", "Completion_Certificate.docx")
        self.output_dir = os.path.join(self.script_dir, "output", "certificates")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def connect_to_sheet(self):
        try:
            # Set up Google Drive and Sheets API scopes
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            
            # Authenticate using the service account JSON key
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            
            # Open the spreadsheet by URL and return the first sheet
            return client.open_by_url(self.sheet_url).get_worksheet(0)
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}")
            return None

    def replace_placeholders(self, doc, data):
        """Replace placeholders EVERYWHERE in the document using multiple methods"""
        
        print(f"{Y}🔍 Searching for placeholders...{W}")
        
        # Method 1: Search in standard paragraphs (body text)
        count = 0
        for paragraph in doc.paragraphs:
            if self._contains_placeholder(paragraph.text, data):
                self._replace_in_paragraph(paragraph, data)
                count += 1
        print(f"   Found {count} in paragraphs")
        
        # Method 2: Search inside tables (cells)
        count = 0
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if self._contains_placeholder(paragraph.text, data):
                            self._replace_in_paragraph(paragraph, data)
                            count += 1
        print(f"   Found {count} in tables")
        
        # Method 3: Direct XML replacement (Crucial for Text Boxes/Shapes)
        count = self._replace_in_xml(doc, data)
        print(f"   Found {count} in XML elements (including text boxes)")

    def _replace_in_xml(self, doc, data):
        """Aggressively replace in ALL XML text nodes to catch floating elements"""
        count = 0
        
        # Access the underlying XML tree of the document
        tree = doc.element
        
        # Iterate over all standard Word text elements (w:t)
        for t_elem in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if t_elem.text:
                original = t_elem.text
                new_text = original
                
                # Check for placeholders in this specific XML node
                for key, value in data.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in new_text:
                        new_text = new_text.replace(placeholder, str(value))
                        count += 1
                
                # Update the XML node text if changed
                if new_text != original:
                    t_elem.text = new_text
        
        # Iterate over DrawingML text elements (a:t) - common in modern Text Boxes
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
        # Helper to check if any key exists in the text string
        return any(f"{{{key}}}" in text for key in data.keys())

    def _replace_in_paragraph(self, paragraph, data):
        """Replace text in paragraph while preserving font styles"""
        original_text = paragraph.text
        new_text = original_text
        
        # Simple string replacement first
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in new_text:
                new_text = new_text.replace(placeholder, str(value))
        
        if new_text == original_text:
            return
        
        # If runs exist, try to preserve formatting of the first run
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
            
            # Clear existing runs
            for _ in range(len(paragraph.runs)):
                paragraph._element.remove(paragraph.runs[0]._element)
            
            # Add new run with the replaced text
            new_run = paragraph.add_run(new_text)
            
            # Re-apply font properties
            new_run.font.name = font_props['name']
            new_run.font.size = font_props['size']
            new_run.font.bold = font_props['bold']
            new_run.font.italic = font_props['italic']
            new_run.font.underline = font_props['underline']
            if font_props['color']:
                new_run.font.color.rgb = font_props['color']

    def generate_certificate_pdf(self, candidate, manual_data):
        full_name = (candidate.get("Full Name(as per Aadhar/PAN)") or "Candidate").strip()
        
        # Create dictionary mapping placeholders to actual values
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

        # 1. Load template and perform replacements
        doc = Document(self.template_docx)
        self.replace_placeholders(doc, data)

        # 2. Sanitize filename to avoid filesystem errors
        safe_name = "".join([c if c.isalnum() or c == '_' else "_" for c in full_name])
        
        # Win32com requires ABSOLUTE paths to work correctly
        docx_path = os.path.abspath(os.path.join(self.output_dir, f"Cert_{safe_name}.docx"))
        pdf_path = os.path.abspath(os.path.join(self.output_dir, f"Cert_{safe_name}.pdf"))

        # 3. Save the modified Word DOCX temporarily
        doc.save(docx_path)
        print(f"{G}✅ DOCX saved: {docx_path}{W}")
        
        # 4. Convert to PDF using MS Word COM Automation (Windows Only)
        try:
            # Initialize COM library
            pythoncom.CoInitialize()
            # Open MS Word in the background
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            
            # Open the generated DOCX file
            wb = word.Documents.Open(docx_path)
            
            # Save as PDF (FileFormat=17 is the code for PDF)
            wb.SaveAs(pdf_path, FileFormat=17)
            wb.Close()
            word.Quit()
            
            # Cleanup - delete the temporary DOCX file if PDF exists
            if os.path.exists(pdf_path):
                print(f"{G}✅ PDF created: {pdf_path}{W}")
                os.remove(docx_path) 
                return pdf_path
            return docx_path
            
        except Exception as e:
            print(f"{R}❌ PDF Error: {e}{W}")
            # Ensure Word quits even if there is an error
            try: 
                word.Quit() 
            except: 
                pass
            return docx_path

    def run_process(self):
        # Connect and fetch data
        sheet = self.connect_to_sheet()
        if not sheet: 
            return
            
        print(f"{Y}⏳ Fetching candidates from sheet...{W}")
        candidates = sheet.get_all_records()

        # Iterate through every candidate in the sheet
        for idx, candidate in enumerate(candidates, 1):
            name = (candidate.get("Full Name(as per Aadhar/PAN)") or "Unknown")
            
            # Print candidate header
            print(f"\n{B}{'='*60}{W}")
            print(f"{B}[{idx}/{len(candidates)}] {name}{W}")
            print(f"{B}{'='*60}{W}")
            
            # Ask user for confirmation
            choice = input(f"Generate Certificate? (y/n/exit): ").strip().lower()
            
            if choice == "exit": 
                break
            if choice != "y": 
                continue
            
            # Get default dates
            today = datetime.now().strftime("%d-%m-%Y")
            sheet_start = candidate.get("Expected Start Date") or candidate.get("Start Date") or ""
            
            # Collect manual inputs with defaults
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
                # Generate the file
                print(f"\n{Y}⚙️  Generating certificate...{W}")
                output_path = self.generate_certificate_pdf(candidate, manual_inputs)
                
                # Success message
                print(f"\n{G}{'='*60}{W}")
                print(f"{G}✅ SUCCESS! Certificate generated:{W}")
                print(f"{G}   {output_path}{W}")
                print(f"{G}{'='*60}{W}\n")
                
            except Exception as e:
                # Error handling
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