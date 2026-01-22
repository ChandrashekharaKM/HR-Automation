# Import necessary libraries
import os
import re
import csv
import requests
from io import StringIO
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load Environment Variables from .env file
load_dotenv()
# Get the registration sheet URL from environment variables
REGISTRATION_SHEET_URL = os.getenv("REGISTRATION_SHEET_URL")
# Define the service account file
SERVICE_ACCOUNT_FILE = 'service_account.json'

# ANSI Color Codes for terminal output
G = '\033[92m'  # Green
R = '\033[91m'  # Red
Y = '\033[93m'  # Yellow
B = '\033[94m'  # Blue
C = '\033[96m'  # Cyan
W = '\033[0m'   # Reset (White)

# Class to manage shortlisting of candidates
class ShortlistManager:
    # Initialize the ShortlistManager with the sheet URL
    def __init__(self, url):
        # Extract spreadsheet ID from the URL
        self.spreadsheet_id = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url).group(1)
        # Extract GID from the URL, default to "0" if not present
        self.gid = re.search(r'gid=([0-9]+)', url).group(1) if 'gid=' in url else "0"
        
        # Authenticate with Google Sheets API using service account credentials
        self.creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.sheet_api = self.service.spreadsheets()
        # Get the sheet name and status column letter
        self.sheet_name = self._get_sheet_name()
        self.status_col = self._get_status_col_letter()

    # Get the sheet name using the GID
    def _get_sheet_name(self):
        meta = self.sheet_api.get(spreadsheetId=self.spreadsheet_id).execute()
        for s in meta['sheets']:
            if str(s['properties']['sheetId']) == self.gid:
                return s['properties']['title']
        return "Sheet1"

    # Get the letter of the "Status" column
    def _get_status_col_letter(self):
        headers = self.sheet_api.values().get(
            spreadsheetId=self.spreadsheet_id, range=f"'{self.sheet_name}'!1:1"
        ).execute().get('values', [[]])[0]
        try:
            idx = headers.index("Status")
        except ValueError:
            idx = 0
        return chr(65 + idx)

    # Fetch pending candidates from the sheet
    def fetch_pending(self):
        csv_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export?format=csv&gid={self.gid}"
        res = requests.get(csv_url)
        reader = csv.DictReader(StringIO(res.text))
        # Return a list of candidates with no status
        return [dict(row, _row=i+2) for i, row in enumerate(reader) if not row.get('Status', '').strip()]

    # Update the status of a candidate in the sheet
    def update_sheet(self, row_num, val):
        self.sheet_api.values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{self.sheet_name}'!{self.status_col}{row_num}",
            valueInputOption='USER_ENTERED',
            body={'values': [[val]]}
        ).execute()

# Main function to run the shortlisting process
def main():
    # Check if the registration sheet URL is provided
    if not REGISTRATION_SHEET_URL:
        print(f"{R}❌ URL missing in .env{W}")
        return

    # Create a ShortlistManager instance
    manager = ShortlistManager(REGISTRATION_SHEET_URL)
    
    # Display the header for the option
    print(f"\n{C}{'='*80}")
    print(f"      OPTION 1: CANDIDATE REGISTRATION & RESUME REVIEW")
    print(f"{'='*80}{W}")

    while True:
        # Fetch pending candidates
        candidates = manager.fetch_pending()
        # If no pending candidates, break the loop
        if not candidates:
            print(f"\n{G}✅ All pending candidates processed!{W}")
            break

        # Iterate through each candidate
        # Iterate through each candidate
        for c in candidates:
            # Get candidate name and resume link
            name = c.get('Name') or c.get('Full Name') or "N/A"
            link = c.get('Resume Link') or c.get('Resume') or "No Link"
            
            # Print candidate information
            print(f"\n{B}SL No. {c['_row']}{W}\t| Name: {Y}{name}{W}\t| Resume: {C}{link}{W}")
            print("-" * 80)
            
            # --- START OF MODIFIED SECTION ---
            while True:
                # Display options for the user
                print(f"{G}1. Shortlist{W}")
                print(f"{R}2. Not Shortlist{W}")
                print(f"{Y}3. Break (Main Menu){W}")
                
                # Get user choice
                choice = input(f"\n👉 {C}Select option (1-3): {W}")
                
                # Process user choice
                if choice == '1':
                    manager.update_sheet(c['_row'], "Resume Shortlisted")
                    print(f"{G}✅ Row {c['_row']} updated: Shortlisted{W}")
                    break  # Valid input, break the while loop to move to next candidate
                elif choice == '2':
                    manager.update_sheet(c['_row'], "Not Shortlisted")
                    print(f"{R}❌ Row {c['_row']} updated: Rejected{W}")
                    break  # Valid input, break the while loop to move to next candidate
                elif choice == '3':
                    print(f"\n{Y}Returning to Main Menu...{W}")
                    return 
                else:
                    # Invalid input: Print error and loop repeats immediately
                    print(f"{R}⚠️ Invalid choice. Please enter 1, 2, or 3.{W}\n")
            # --- END OF MODIFIED SECTION ---

        # Refresh the candidate list
        print(f"\n{B}--- Refreshing Candidate List ---{W}")

# Entry point of the script
if __name__ == "__main__":
    main()
