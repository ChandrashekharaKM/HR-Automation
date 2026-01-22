import os
import smtplib
import gspread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

# ANSI colors for terminal output
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class OfferEmailSender:
    def __init__(self):
        # Set the script directory as the base path
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load environment variables from the parent directory
        load_dotenv(os.path.join(self.script_dir, "..", ".env"))

        # Define paths for credentials and resources
        self.creds_file = os.path.join(self.script_dir, "service_account.json")
        self.reg_sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        
        # Load social media links from .env (with defaults)
        self.ig_link = os.getenv("INSTAGRAM_URL", "#")
        self.li_link = os.getenv("LINKEDIN_URL", "#")
        self.web_link = os.getenv("WEBSITE_URL", "#")

        # Set paths for the HTML template and the PDF output folder
        self.template_path = os.path.join(self.script_dir, "templates", "offer_email_template.html")
        self.offer_dir = os.path.join(self.script_dir, "output", "offer_letters")
        self.worksheet = None

    def connect(self):
        try:
            # Authenticate with Google Sheets API
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            # Open the sheet by URL and select the first tab
            self.worksheet = client.open_by_url(self.reg_sheet_url).get_worksheet(0)
            return True
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}"); return False

    def fetch_data_safely(self):
        # Get all raw values from the sheet
        data = self.worksheet.get_all_values()
        if not data: return []
        
        # Handle empty headers by generating generic names (col_1, col_2, etc.)
        headers = [h.strip() if h.strip() else f"col_{i}" for i, h in enumerate(data[0])]
        
        # Map rows to dictionaries using the cleaned headers
        return [dict(zip(headers, row), _row=i+1) for i, row in enumerate(data[1:], 1)]

    def send_offer_email(self, candidate, manual_data):
        # Extract candidate name and email safely
        full_name = (candidate.get("Full Name(as per Aadhar/PAN)") or candidate.get("Name") or "Candidate").strip()
        recipient_email = (candidate.get("Email address") or candidate.get("Email")).strip()
        
        # Generate the expected PDF filename (sanitized to match the generator script)
        safe_name = "".join([c if c.isalnum() else "_" for c in full_name])
        pdf_path = os.path.join(self.offer_dir, f"Offer_{safe_name}.pdf")

        # Verify the PDF exists before trying to attach it
        if not os.path.exists(pdf_path):
            print(f"{R}❌ PDF missing for {full_name}. Run Option 6 first.{W}")
            return False

        # Create the email container
        msg = MIMEMultipart()
        msg['From'] = f"Team SwipeGen <{self.sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = "Journey with SwipeGen begins now!"

        # Read the HTML template and fill in dynamic data
        with open(self.template_path, "r", encoding="utf-8") as f:
            html_content = f.read().format(
                name=full_name.split()[0], # Use first name only
                role=manual_data['role'],
                start_date=manual_data['start_date'],
                ig_link=self.ig_link, li_link=self.li_link, web_link=self.web_link
            )
        msg.attach(MIMEText(html_content, 'html'))

        # Attach the PDF file
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename=Offer_{safe_name}.pdf")
            msg.attach(part)

        # Connect to Gmail SMTP and send
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(self.sender_email, self.sender_password)
        server.sendmail(self.sender_email, recipient_email, msg.as_string())
        server.quit()
        return True

    def run_process(self):
        # Connect to the sheet
        if not self.connect(): return
        
        # Fetch data and filter for candidates marked as 'Hired'
        records = self.fetch_data_safely()
        hired = [r for r in records if str(r.get("Status", "")).strip() == "Hired"]

        if not hired:
            print(f"{Y}⚠️ No candidates marked 'Hired' found.{W}"); return

        # Process each hired candidate
        for candidate in hired:
            name = candidate.get("Full Name(as per Aadhar/PAN)") or candidate.get("Name")
            print(f"\n{B}Candidate: {Y}{name}{W}")
            
            # Ask user for confirmation
            if input(f"{C}Send HTML Offer Email? (y/n): {W}").lower() != 'y': continue

            # Get manual inputs for the email body
            m_role = input("💼 Role [Software Developer - Intern]: ") or "Software Developer - Intern"
            m_start = input("🗓️  Start Date [December 24, 2025]: ") or "December 24, 2025"

            # Attempt to send email
            if self.send_offer_email(candidate, {'role': m_role, 'start_date': m_start}):
                # If successful, find the 'Status' column index dynamically and update it
                headers = self.worksheet.row_values(1)
                status_col = next(i for i, h in enumerate(headers, 1) if "status" in h.lower())
                
                # Update status to 'Internship Ongoing' to prevent duplicate processing
                self.worksheet.update_cell(candidate['_row'], status_col, "Internship Ongoing")
                print(f"{G}✅ Sent and status updated!{W}")

def main():
    OfferEmailSender().run_process()

if __name__ == "__main__":
    main()