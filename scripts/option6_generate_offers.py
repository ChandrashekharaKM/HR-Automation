import os
import gspread
from docx import Document
from docx2pdf import convert
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# Define ANSI colors for terminal output (Green, Red, Yellow, Blue, Cyan, White)
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class OfferLetterGenerator:
    def __init__(self):
        # Determine the directory where this script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load environment variables from the .env file in the parent directory
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))
        
        # Set path to the Google Service Account JSON key
        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        
        # Get the Google Sheet URL from environment variables
        self.sheet_url = os.getenv("OFFER_DETAILS_SHEET_URL")
        
        # Set path to the Word document template
        self.template_docx = os.path.join(self.script_dir, "templates", "offer_template.docx")
        
        # Define the output directory and create it if it doesn't exist
        self.output_dir = os.path.join(self.script_dir, "output", "offer_letters")
        os.makedirs(self.output_dir, exist_ok=True)

    def connect_to_sheet(self):
        try:
            # Define scopes required for Google Sheets and Drive API
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            
            # Authenticate using the service account credentials
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            
            # Open the sheet by URL and return the first worksheet
            return client.open_by_url(self.sheet_url).get_worksheet(0)
        except Exception as e:
            # Print error message if connection fails
            print(f"{R}❌ Connection Error: {e}{W}")
            return None

    def replace_placeholders(self, doc, data):
        """Enhanced replacement that handles split runs in Word to preserve formatting"""
        
        # Iterate through all standard paragraphs in the document body
        for paragraph in doc.paragraphs:
            if self._contains_placeholder(paragraph.text, data):
                self._replace_in_paragraph(paragraph, data)
        
        # Iterate through all tables, rows, and cells to find text
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if self._contains_placeholder(paragraph.text, data):
                            self._replace_in_paragraph(paragraph, data)

    def _contains_placeholder(self, text, data):
        """Check if the text contains any key from the data dictionary wrapped in {}"""
        return any(f"{{{key}}}" in text for key in data.keys())

    def _replace_in_paragraph(self, paragraph, data):
        """Replace placeholders while attempting to preserve the original font style"""
        
        # Get the full text of the paragraph
        original_text = paragraph.text
        new_text = original_text
        
        # Perform string replacement for all keys in the data dictionary
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in new_text:
                new_text = new_text.replace(placeholder, str(value))
        
        # If no changes were made, exit the function
        if new_text == original_text:
            return
        
        # If the paragraph has existing runs (text chunks with specific styling)
        if paragraph.runs:
            # Capture style properties from the very first run
            first_run = paragraph.runs[0]
            font_props = {
                'name': first_run.font.name,
                'size': first_run.font.size,
                'bold': first_run.font.bold,
                'italic': first_run.font.italic,
                'underline': first_run.font.underline,
                'color': first_run.font.color.rgb if first_run.font.color else None
            }
            
            # Remove all existing runs (clearing the text but keeping paragraph settings)
            for _ in range(len(paragraph.runs)):
                paragraph._element.remove(paragraph.runs[0]._element)
            
            # Add a single new run containing the fully replaced text
            new_run = paragraph.add_run(new_text)
            
            # Re-apply the captured font properties to the new run
            new_run.font.name = font_props['name']
            new_run.font.size = font_props['size']
            new_run.font.bold = font_props['bold']
            new_run.font.italic = font_props['italic']
            new_run.font.underline = font_props['underline']
            if font_props['color']:
                new_run.font.color.rgb = font_props['color']

    def generate_offer_pdf(self, candidate, manual_data):
        # Extract candidate name safely
        full_name = (candidate.get("Full Name(as per Aadhar/PAN)") or "Candidate").strip()
        
        # combine manual inputs with candidate name for replacement
        data = {
            "FULL_NAME": full_name,
            "ROLE": manual_data['role'],
            "DATE": manual_data['date'],
            "PLACE": manual_data['place'],
            "START_DATE": manual_data['start_date']
        }

        # Load the Word template
        doc = Document(self.template_docx)
        # Perform the text replacement
        self.replace_placeholders(doc, data)

        # Create a safe filename (remove special characters)
        safe_name = "".join([c if c.isalnum() or c == '_' else "_" for c in full_name])
        docx_path = os.path.join(self.output_dir, f"Offer_{safe_name}.docx")
        pdf_path = os.path.join(self.output_dir, f"Offer_{safe_name}.pdf")

        # Save the modified Word document temporarily
        doc.save(docx_path)
        
        # Convert the Word document to PDF
        try:
            convert(docx_path, pdf_path)
            # If PDF creation is successful, delete the temporary Word file
            if os.path.exists(pdf_path):
                os.remove(docx_path)
                return pdf_path
            return docx_path
        except Exception as e:
            # Fallback: Return DOCX path if PDF conversion fails
            print(f"{R}❌ PDF Error: {e}{W}")
            return docx_path

    def run_process(self):
        # Connect to Google Sheets
        sheet = self.connect_to_sheet()
        if not sheet: 
            return
            
        # Fetch all records as a list of dictionaries
        candidates = sheet.get_all_records()

        # Iterate through candidates with an index counter
        for idx, candidate in enumerate(candidates, 1):
            name = (candidate.get("Full Name(as per Aadhar/PAN)") or "Unknown")
            
            # Display candidate progress
            print(f"\n{B}[{idx}/{len(candidates)}] {name}{W}")
            
            # Ask user if they want to generate offer for this person
            choice = input(f"Generate? (y/n/exit): ").strip().lower()
            
            if choice == "exit": 
                break
            if choice != "y": 
                continue
            
            # Collect manual inputs with default fallbacks
            today = datetime.now().strftime("%B %d, %Y")
            m_date = input(f"📅 Date [{today}]: ").strip() or today
            m_place = input(f"📍 Place [Bengaluru]: ").strip() or "Bengaluru"
            m_role = input(f"💼 Role [Software Developer - Intern]: ").strip() or "Software Developer - Intern"
            
            # Get expected start date from sheet, or use TBD
            expected_start = candidate.get("Expected Start Date", "TBD")
            m_start = input(f"🗓️  Start Date [{expected_start}]: ").strip() or str(expected_start)

            # Dictionary of manual inputs
            manual_inputs = {
                'date': m_date, 
                'place': m_place, 
                'role': m_role, 
                'start_date': m_start
            }

            # Attempt to generate the document
            try:
                print(f"{Y}⚙️  Generating...{W}", end=" ", flush=True)
                output_path = self.generate_offer_pdf(candidate, manual_inputs)
                print(f"{G}✓{W}")
                print(f"{G}✅ {output_path}{W}")
                
            except Exception as e:
                print(f"{R}✗{W}")
                print(f"{R}❌ Failed: {e}{W}")

def main():
    # Print header and start the generator
    print(f"{B}📄 SwipeGen Offer Letter Generator{W}\n")
    generator = OfferLetterGenerator()
    generator.run_process()
    print(f"\n{G}✨ Done!{W}")
    # Keep terminal open until user presses Enter
    input(f"{C}Press Enter to exit...{W}")

if __name__ == "__main__":
    main()