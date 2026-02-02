import os
import re
import gspread
from docx import Document
from docx2pdf import convert
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class OfferLetterGenerator:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))
        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        self.sheet_url = os.getenv("OFFER_DETAILS_SHEET_URL")
        self.template_docx = os.path.join(self.script_dir, "templates", "offer_template.docx")
        self.output_dir = os.path.join(self.script_dir, "output", "offer_letters")
        os.makedirs(self.output_dir, exist_ok=True)

    def connect_to_sheet(self):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            
            # Open the spreadsheet
            spreadsheet = client.open_by_url(self.sheet_url)
            
            # SMART FIX: Check for GID in URL
            gid_match = re.search(r'gid=([0-9]+)', self.sheet_url)
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        print(f"{G}✅ Connected to tab: {sheet.title}{W}")
                        return sheet

            # Fallback
            return spreadsheet.get_worksheet(0)
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}")
            return None

    def replace_placeholders(self, doc, data):
        for paragraph in doc.paragraphs:
            if self._contains_placeholder(paragraph.text, data):
                self._replace_in_paragraph(paragraph, data)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if self._contains_placeholder(paragraph.text, data):
                            self._replace_in_paragraph(paragraph, data)

    def _contains_placeholder(self, text, data):
        return any(f"{{{key}}}" in text for key in data.keys())

    def _replace_in_paragraph(self, paragraph, data):
        original_text = paragraph.text
        new_text = original_text
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in new_text:
                new_text = new_text.replace(placeholder, str(value))
        if new_text == original_text: return
        
        if paragraph.runs:
            first_run = paragraph.runs[0]
            font_props = {
                'name': first_run.font.name, 'size': first_run.font.size,
                'bold': first_run.font.bold, 'italic': first_run.font.italic,
                'underline': first_run.font.underline,
                'color': first_run.font.color.rgb if first_run.font.color else None
            }
            for _ in range(len(paragraph.runs)):
                paragraph._element.remove(paragraph.runs[0]._element)
            new_run = paragraph.add_run(new_text)
            new_run.font.name = font_props['name']
            new_run.font.size = font_props['size']
            new_run.font.bold = font_props['bold']
            new_run.font.italic = font_props['italic']
            new_run.font.underline = font_props['underline']
            if font_props['color']: new_run.font.color.rgb = font_props['color']

    def generate_offer_pdf(self, candidate, manual_data):
        full_name = (candidate.get("Full Name(as per Aadhar/PAN)") or "Candidate").strip()
        data = {
            "FULL_NAME": full_name, "ROLE": manual_data['role'],
            "DATE": manual_data['date'], "PLACE": manual_data['place'],
            "START_DATE": manual_data['start_date']
        }
        doc = Document(self.template_docx)
        self.replace_placeholders(doc, data)
        safe_name = "".join([c if c.isalnum() or c == '_' else "_" for c in full_name])
        docx_path = os.path.join(self.output_dir, f"Offer_{safe_name}.docx")
        pdf_path = os.path.join(self.output_dir, f"Offer_{safe_name}.pdf")
        doc.save(docx_path)
        try:
            convert(docx_path, pdf_path)
            if os.path.exists(pdf_path):
                os.remove(docx_path)
                return pdf_path
            return docx_path
        except Exception as e:
            print(f"{R}❌ PDF Error: {e}{W}")
            return docx_path

    def run_process(self):
        sheet = self.connect_to_sheet()
        if not sheet: return
        candidates = sheet.get_all_records()
        for idx, candidate in enumerate(candidates, 1):
            name = (candidate.get("Full Name(as per Aadhar/PAN)") or "Unknown")
            print(f"\n{B}[{idx}/{len(candidates)}] {name}{W}")
            choice = input(f"Generate? (y/n/exit): ").strip().lower()
            if choice == "exit": break
            if choice != "y": continue
            
            today = datetime.now().strftime("%B %d, %Y")
            m_date = input(f"📅 Date [{today}]: ").strip() or today
            m_place = input(f"📍 Place [Bengaluru]: ").strip() or "Bengaluru"
            m_role = input(f"💼 Role [Software Developer - Intern]: ").strip() or "Software Developer - Intern"
            expected_start = candidate.get("Expected Start Date", "TBD")
            m_start = input(f"🗓️  Start Date [{expected_start}]: ").strip() or str(expected_start)
            manual_inputs = {'date': m_date, 'place': m_place, 'role': m_role, 'start_date': m_start}

            try:
                print(f"{Y}⚙️  Generating...{W}", end=" ", flush=True)
                output_path = self.generate_offer_pdf(candidate, manual_inputs)
                print(f"{G}✅ {output_path}{W}")
            except Exception as e:
                print(f"{R}❌ Failed: {e}{W}")

# Added main function wrapper so the menu can import it
def main():
    print(f"{B}📄 SwipeGen Offer Letter Generator{W}\n")
    generator = OfferLetterGenerator()
    generator.run_process()
    print(f"\n{G}✨ Done!{W}")

if __name__ == "__main__":
    main()