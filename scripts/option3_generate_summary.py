# Import necessary libraries
import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from dotenv import load_dotenv

# ANSI Color Codes for terminal output
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

# Class to generate a recruitment summary
class RecruitmentSummarizer:
    # Initialize the RecruitmentSummarizer
    def __init__(self):
        # Load environment variables from .env file
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(dotenv_path)

        # Set file paths and get URLs from environment variables
        self.creds_file = os.path.join(os.path.dirname(__file__), "service_account.json")
        self.reg_url = os.getenv("REGISTRATION_SHEET_URL") or os.getenv("SHEET_URL")
        self.int_url = os.getenv("INTERVIEW_RESPONSE_SHEET_URL")
        
        # Set scope for Google Sheets API
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Check if credentials file exists
        if not os.path.exists(self.creds_file):
            raise FileNotFoundError(f"Missing {self.creds_file} in scripts folder")
            
        # Authorize credentials and create a client
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, self.scope)
        self.client = gspread.authorize(self.creds)

    # Get a worksheet from a Google Sheet URL
    def get_sheet(self, url):
        try:
            if not url: return None
            # Extract spreadsheet ID from the URL
            match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
            if not match: return None
            # Open the worksheet
            return self.client.open_by_key(match.group(1)).get_worksheet(0)
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}")
            return None

    # Normalize email for better matching
    def normalize_email(self, email):
        """Normalize email for better matching - extract username part before @"""
        email = str(email).strip().lower()
        if '@' in email:
            # Extract username part (before @) for fuzzy matching
            username = email.split('@')[0]
            return email, username
        return email, email

    # Run the report generation process
    def run_report(self):
        print(f"\n{C}{'='*65}\n📊 RECRUITMENT STATUS SUMMARY & SYNC\n{'='*65}{W}")

        # Get registration and interview sheets
        reg_sheet = self.get_sheet(self.reg_url)
        int_sheet = self.get_sheet(self.int_url)

        if not reg_sheet or not int_sheet:
            print(f"{R}❌ Error: One or both sheets could not be reached.{W}")
            return

        # Get all records from the sheets
        reg_records = reg_sheet.get_all_records()
        int_records = int_sheet.get_all_records()

        # Registration Sheet Setup
        reg_headers = [h.strip() for h in reg_sheet.row_values(1)]
        email_key = next((h for h in reg_headers if "email" in h.lower()), None)
        status_col_idx = next((i for i, h in enumerate(reg_headers, 1) if "status" in h.lower()), None)

        # 1. Map Interview Responses - Build comprehensive map
        interview_map = {}  # Maps both full email and username
        
        print(f"{Y}📥 Processing interview responses...{W}")
        for row in int_records:
            email = str(row.get('Email address', row.get('Email', ''))).strip().lower()
            
            # Find the availability column
            avail_key = next((k for k in row.keys() if "available for the interview" in k.lower()), None)
            resp = str(row.get(avail_key, '')).strip() if avail_key else ""
            
            if email and resp:
                full_email, username = self.normalize_email(email)
                interview_map[full_email] = resp
                interview_map[username] = resp  # Also store by username for fuzzy matching
                print(f"  📝 Found response from: {email} -> {resp}")

        stats = {'applied': len(reg_records), 'shortlisted': 0, 'accepted': 0, 'declined': 0}

        print(f"\n{Y}🔄 Processing registration updates...{W}")
        
        updates_made = 0
        no_match_count = 0
        
        for i, row in enumerate(reg_records, start=2):
            email = str(row.get(email_key, '')).strip().lower()
            current_status = str(row.get('Status', '')).strip()

            # Identify anyone who was shortlisted/invited
            is_shortlisted = any(term in current_status for term in ["Shortlisted", "Invited", "Accepted", "Declined"])
            if is_shortlisted:
                stats['shortlisted'] += 1

            # 2. Match Response from Form - Try both full email and username
            full_email, username = self.normalize_email(email)
            user_choice = None
            
            # Try exact email match first, then username match
            if full_email in interview_map:
                user_choice = interview_map[full_email]
            elif username in interview_map:
                user_choice = interview_map[username]
            
            if user_choice:
                user_choice_lower = user_choice.lower()
                
                # Check for "Yes, I am available." or any yes+available combination
                if "yes" in user_choice_lower and "available" in user_choice_lower:
                    target_status = "Interview Accepted"
                else:
                    target_status = "Interview Declined"

                # Update main registration sheet status
                if current_status != target_status:
                    try:
                        reg_sheet.update_cell(i, status_col_idx, target_status)
                        current_status = target_status
                        updates_made += 1
                        print(f"{G}✅ Updated {email} -> {target_status}{W}")
                    except Exception as e:
                        print(f"{R}❌ Failed to update {email}: {e}{W}")
            elif is_shortlisted:
                no_match_count += 1
                print(f"{Y}⚠️  No interview response found for: {email}{W}")
            
            # 3. Final Tallying
            if current_status == "Interview Accepted":
                stats['accepted'] += 1
            elif is_shortlisted and current_status != "Interview Accepted":
                stats['declined'] += 1

        # 4. Final Formatted Report
        print(f"\n{G}✨ Total Updates Made: {updates_made}{W}")
        if no_match_count > 0:
            print(f"{Y}⚠️  Candidates without interview response: {no_match_count}{W}")
        
        print(f"\n{B}{'='*65}\n📈 FINAL RECRUITMENT REPORT\n{'='*65}{W}")
        print(f"{ 'Metric':<40} | {'Count':<10}")
        print("-" * 65)
        print(f"{ 'Total Candidates Applied':<40} | {C}{stats['applied']:<10}{W}")
        print(f"{ 'Total Candidates Shortlisted':<40} | {Y}{stats['shortlisted']:<10}{W}")
        print(f"{ 'Interview Invites Accepted':<40} | {G}{stats['accepted']:<10}{W}")
        print(f"{ 'Interview Invites Declined/Hold':<40} | {R}{stats['declined']:<10}{W}")
        print(f"{B}{'='*65}{W}\n")

# Main function to run the summarizer
def main():
    try:
        summarizer = RecruitmentSummarizer()
        summarizer.run_report()
    except Exception as e:
        print(f"{R}Error: {e}{W}")

# Entry point of the script
if __name__ == "__main__":
    main()
