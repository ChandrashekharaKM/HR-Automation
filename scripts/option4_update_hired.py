import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class HiringManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.base_dir, '..', '.env'))
        self.creds_file = os.path.join(self.base_dir, "service_account.json")
        self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.worksheet = None

    def connect(self):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_url(self.sheet_url)
            
            # Smart Tab Detection
            gid_match = re.search(r'gid=([0-9]+)', self.sheet_url)
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        self.worksheet = sheet
                        return True
            self.worksheet = spreadsheet.get_worksheet(0)
            return True
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}"); return False

    def fetch_interviewed(self):
        try:
            data = self.worksheet.get_all_values()
            if not data: return []
            headers = [h.strip() if h.strip() else f"empty_{i}" for i, h in enumerate(data[0])]
            candidates = []
            for i, row in enumerate(data[1:], 1):
                row_dict = dict(zip(headers, row))
                if str(row_dict.get('Status', '')).strip() == "Interview Accepted":
                    row_dict['_row'] = i + 1
                    candidates.append(row_dict)
            return candidates
        except Exception as e:
            print(f"{R}❌ Error fetching data: {e}{W}"); return []

    def update_status(self, row_idx, status):
        try:
            headers = self.worksheet.row_values(1)
            status_col = next(i for i, h in enumerate(headers, 1) if "status" in h.lower())
            self.worksheet.update_cell(row_idx, status_col, status)
            return True
        except Exception as e:
            print(f"{R}❌ Update failed: {e}{W}"); return False

def main():
    manager = HiringManager()
    if not manager.connect(): return
    while True:
        candidates = manager.fetch_interviewed()
        if not candidates:
            print(f"\n{G}✅ No pending 'Interview Accepted' candidates.{W}")
            break
        for c in candidates:
            name = c.get('Name') or c.get('Full Name') or "N/A"
            email = c.get('Email address') or c.get('Email') or "N/A"
            print(f"\n{B}Candidate: {Y}{name}{W} | {email}")
            print(f"{G}1. Hired{W} | {R}2. Reject{W} | {Y}3. Exit{W}")
            choice = input(f"👉 Decision: ").strip()
            if choice == '1':
                if manager.update_status(c['_row'], "Hired"): print(f"{G}✨ HIRED{W}")
            elif choice == '2':
                if manager.update_status(c['_row'], "Rejected"): print(f"{R}❌ REJECTED{W}")
            elif choice == '3': return
        print(f"\n{B}--- Refreshing ---{W}")

if __name__ == "__main__":
    main()