import os
import re
import csv
import requests
from io import StringIO
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load Environment Variables
load_dotenv()
REGISTRATION_SHEET_URL = os.getenv("REGISTRATION_SHEET_URL")
SERVICE_ACCOUNT_FILE = 'service_account.json'

# ANSI Color Codes
G = '\033[92m'  # Green
R = '\033[91m'  # Red
Y = '\033[93m'  # Yellow
B = '\033[94m'  # Blue
C = '\033[96m'  # Cyan
W = '\033[0m'   # Reset (White)

class ShortlistManager:
    def __init__(self, url):
        self.spreadsheet_id = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url).group(1)
        self.gid = re.search(r'gid=([0-9]+)', url).group(1) if 'gid=' in url else "0"
        
        self.creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.sheet_api = self.service.spreadsheets()
        self.sheet_name = self._get_sheet_name()
        self.status_col = self._get_status_col_letter()

    def _get_sheet_name(self):
        meta = self.sheet_api.get(spreadsheetId=self.spreadsheet_id).execute()
        for s in meta['sheets']:
            if str(s['properties']['sheetId']) == self.gid:
                return s['properties']['title']
        return "Sheet1"

    def _get_status_col_letter(self):
        headers = self.sheet_api.values().get(
            spreadsheetId=self.spreadsheet_id, range=f"'{self.sheet_name}'!1:1"
        ).execute().get('values', [[]])[0]
        idx = headers.index("Status") if "Status" in headers else 0
        return chr(65 + idx)

    def fetch_pending(self):
        csv_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export?format=csv&gid={self.gid}"
        res = requests.get(csv_url)
        reader = csv.DictReader(StringIO(res.text))
        return [dict(row, _row=i+2) for i, row in enumerate(reader) if not row.get('Status', '').strip()]

    def update_sheet(self, row_num, val):
        self.sheet_api.values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{self.sheet_name}'!{self.status_col}{row_num}",
            valueInputOption='USER_ENTERED',
            body={'values': [[val]]}
        ).execute()

def main():
    if not REGISTRATION_SHEET_URL:
        print(f"{R}❌ URL missing in .env{W}")
        return

    manager = ShortlistManager(REGISTRATION_SHEET_URL)
    
    print(f"\n{C}{'='*80}")
    print(f"      OPTION 1: CANDIDATE REGISTRATION & RESUME REVIEW")
    print(f"{'='*80}{W}")

    while True:
        candidates = manager.fetch_pending()
        if not candidates:
            print(f"\n{G}✅ All pending candidates processed!{W}")
            break

        for c in candidates:
            name = c.get('Name') or c.get('Full Name') or "N/A"
            link = c.get('Resume Link') or c.get('Resume') or "No Link"
            
            # Colored Info Line
            print(f"\n{B}SL No. {c['_row']}{W}\t| Name: {Y}{name}{W}\t| Resume: {C}{link}{W}")
            print("-" * 80)
            
            # Colored Options
            print(f"{G}1. Shortlist{W}")
            print(f"{R}2. Not Shortlist{W}")
            print(f"{Y}3. Break (Main Menu){W}")
            
            choice = input(f"\n👉 {C}Select option (1-3): {W}")
            
            if choice == '1':
                manager.update_sheet(c['_row'], "Resume Shortlisted")
                print(f"{G}✅ Row {c['_row']} updated: Shortlisted{W}")
            elif choice == '2':
                manager.update_sheet(c['_row'], "Not Shortlisted")
                print(f"{R}❌ Row {c['_row']} updated: Rejected{W}")
            elif choice == '3':
                print(f"\n{Y}Returning to Main Menu...{W}")
                return 
            else:
                print(f"{R}⚠️ Invalid choice, skipping to next...{W}")
        
        print(f"\n{B}--- Refreshing Candidate List ---{W}")

if __name__ == "__main__":
    main()