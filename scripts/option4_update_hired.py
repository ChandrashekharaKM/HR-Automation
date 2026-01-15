import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# ANSI Color Codes
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class HiringManager:
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(dotenv_path)
        self.creds_file = os.path.join(os.path.dirname(__file__), "service_account.json")
        self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.worksheet = None

    def connect(self):
        try:
            match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', self.sheet_url)
            if not match: return False
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            self.worksheet = client.open_by_key(match.group(1)).get_worksheet(0)
            return True
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}")
            return False

    def fetch_interviewed(self):
        """Fetches records safely without crashing on empty headers"""
        try:
            # Get all values from the sheet
            data = self.worksheet.get_all_values()
            if not data: return []

            # Extract headers and handle duplicates/blanks
            raw_headers = data[0]
            headers = []
            for i, h in enumerate(raw_headers):
                # If header is blank, give it a placeholder name to avoid GSpreadException
                val = h.strip() if h.strip() else f"empty_col_{i}"
                headers.append(val)

            # Convert rows to dictionaries
            rows = data[1:]
            candidates = []
            for i, row_vals in enumerate(rows):
                # Create dict only for the length of actual data columns
                row_dict = dict(zip(headers, row_vals))
                
                # Check for "Interview Accepted" status
                if str(row_dict.get('Status', '')).strip() == "Interview Accepted":
                    row_dict['_row'] = i + 2 # +2 because 0-based index and header row
                    candidates.append(row_dict)
            
            return candidates
        except Exception as e:
            print(f"{R}❌ Error fetching data: {e}{W}")
            return []

    def update_status(self, row_idx, status):
        try:
            headers = self.worksheet.row_values(1)
            status_col = next(i for i, h in enumerate(headers, 1) if "status" in h.lower())
            self.worksheet.update_cell(row_idx, status_col, status)
            return True
        except Exception as e:
            print(f"{R}❌ Update failed: {e}{W}")
            return False

def main():
    manager = HiringManager()
    if not manager.connect(): return

    while True:
        candidates = manager.fetch_interviewed()
        if not candidates:
            print(f"\n{G}✅ No candidates currently pending decision (Status: Interview Accepted).{W}")
            break

        for c in candidates:
            name = c.get('Name') or c.get('Full Name') or "N/A"
            email = c.get('Email address') or c.get('Email') or "N/A"
            
            print(f"\n{B}Candidate Information:{W}")
            print(f"SL No. {c['_row']} | Name: {Y}{name}{W} | Email: {C}{email}{W}")
            print("-" * 80)
            print(f"{G}1. Hired{W}")
            print(f"{R}2. Reject{W}")
            print(f"{Y}3. Back{W}")
            
            choice = input(f"\n👉 {C}Select decision for {name}: {W}").strip()

            if choice == '1':
                if manager.update_status(c['_row'], "Hired"):
                    print(f"{G}✨ Row {c['_row']} updated: HIRED{W}")
            elif choice == '2':
                if manager.update_status(c['_row'], "Rejected"):
                    print(f"{R}❌ Row {c['_row']} updated: REJECTED{W}")
            elif choice == '3':
                return
            else:
                print(f"{R}⚠️ Invalid choice, skipping...{W}")
        
        print(f"\n{B}--- Refreshing Candidate List ---{W}")

if __name__ == "__main__":
    main()