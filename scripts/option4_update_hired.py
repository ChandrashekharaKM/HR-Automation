import os
import re
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Terminal Colors
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class HiringManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.base_dir, '..', '.env'))
        
        self.creds_file = os.path.join(self.base_dir, "service_account.json")
        self.sheet_url = os.getenv("REGISTRATION_SHEET_URL")
        self.response_url = os.getenv("INTERVIEW_RESPONSE_SHEET_URL")
        
        self.worksheet = None
        self.resp_sheet = None

    def _get_sheet_by_url(self, client, url):
        """Helper to find the specific tab using GID from URL"""
        try:
            spreadsheet = client.open_by_url(url)
            gid_match = re.search(r'gid=([0-9]+)', url)
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        return sheet
            return spreadsheet.get_worksheet(0)
        except Exception as e:
            print(f"{R}❌ Error opening sheet ({url}): {e}{W}")
            return None

    def connect(self):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            
            self.worksheet = self._get_sheet_by_url(client, self.sheet_url)
            if self.response_url:
                self.resp_sheet = self._get_sheet_by_url(client, self.response_url)
            
            return True if self.worksheet else False
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}"); return False

    def get_confirmed_emails(self):
        """Fetches emails from Response Sheet where answer matches 'Yes'"""
        if not self.resp_sheet: return set()
        try:
            print(f"{Y}⏳ Checking Response Sheet for 'Yes' responses...{W}")
            responses = self.resp_sheet.get_all_records()
            yes_emails = set()
            for row in responses:
                avail_key = next((k for k in row.keys() if "available" in k.lower()), None)
                email = str(row.get('Email address', row.get('Email', ''))).strip().lower()
                if avail_key and "yes" in str(row[avail_key]).lower():
                    yes_emails.add(email)
            print(f"{G}   Found {len(yes_emails)} candidates who said 'Yes'.{W}")
            return yes_emails
        except Exception as e:
            print(f"{R}❌ Error reading Response Sheet: {e}{W}"); return set()

    def fetch_processable_candidates(self, yes_emails):
        """Fetches candidates from Registration Sheet who are Accepted and said Yes"""
        try:
            data = self.worksheet.get_all_values()
            if not data: return []
            headers = [h.strip() if h.strip() else f"col_{i}" for i, h in enumerate(data[0])]
            candidates = []
            for i, row in enumerate(data[1:], 1):
                row_dict = dict(zip(headers, row))
                email = str(row_dict.get('Email address', row_dict.get('Email', ''))).strip().lower()
                status = str(row_dict.get('Status', '')).strip().lower()
                if email in yes_emails and "interview accepted" in status:
                    row_dict['_row'] = i + 1
                    candidates.append(row_dict)
            return candidates
        except Exception as e:
            print(f"{R}❌ Error fetching data: {e}{W}"); return []

    def update_hired_status(self, row_idx, start_date, end_date):
        """Updates Registration Sheet status to Hired with dates"""
        try:
            headers = self.worksheet.row_values(1)
            status_col = next(i for i, h in enumerate(headers, 1) if "status" in h.lower())
            start_col = next(i for i, h in enumerate(headers, 1) if "start" in h.lower() and "date" in h.lower())
            end_col = next(i for i, h in enumerate(headers, 1) if "end" in h.lower() and "date" in h.lower())
            self.worksheet.update_cell(row_idx, status_col, "Hired")
            self.worksheet.update_cell(row_idx, start_col, start_date)
            self.worksheet.update_cell(row_idx, end_col, end_date)
            return True
        except Exception as e:
            print(f"{R}❌ Update error: {e}{W}"); return False

    def update_status_only(self, row_idx, status):
        """Updates Registration Sheet status for Rejections"""
        try:
            headers = self.worksheet.row_values(1)
            status_col = next(i for i, h in enumerate(headers, 1) if "status" in h.lower())
            self.worksheet.update_cell(row_idx, status_col, status)
            return True
        except Exception as e:
            print(f"{R}❌ Status update error: {e}{W}"); return False

    def delete_response_row(self, email):
        """Deletes matching row from Interview Response Sheet"""
        if not self.resp_sheet: return False
        try:
            records = self.resp_sheet.get_all_records()
            for i, row in enumerate(records, start=2):
                row_email = str(row.get('Email address', row.get('Email', ''))).strip().lower()
                if row_email == email.strip().lower():
                    self.resp_sheet.delete_rows(i)
                    print(f"{R}🗑️  Entry removed from Response Sheet.{W}")
                    return True
            return False
        except Exception as e:
            print(f"{R}❌ Delete error: {e}{W}"); return False

def main():
    manager = HiringManager()
    if not manager.connect(): return
    
    yes_emails = manager.get_confirmed_emails()
    if not yes_emails:
        print(f"\n{Y}⚠️  No candidates have replied 'Yes' in the response sheet.{W}"); return

    candidates = manager.fetch_processable_candidates(yes_emails)
    if not candidates:
        print(f"\n{G}✅ No pending 'Interview Accepted' candidates.{W}"); return

    print(f"\n{B}--- Processing {len(candidates)} Candidates ---{W}")
    
    for c in candidates:
        name = c.get('Name') or c.get('Full Name') or "N/A"
        email = c.get('Email address') or c.get('Email') or "N/A"
        auto_start = c.get('Expected Start Date') or c.get('Start Date') or datetime.now().strftime("%d-%m-%Y")

        print(f"\n{B}Candidate: {Y}{name}{W} | {email}")
        print("-" * 50)
        print(f"{G}1. Hired (Updates Registration & Deletes Response){W}")
        print(f"{R}2. Reject (Updates Registration & Deletes Response){W}")
        print(f"{Y}3. Exit{W}")
        
        choice = input(f"👉 Decision: ").strip()
        
        if choice == '1':
            use_auto = input(f"   Use suggested date {auto_start}? (y/n): ").strip().lower()
            m_start = auto_start if use_auto == 'y' else input("   🗓️  Start Date: ").strip()
            m_end = input("   🏁 End Date: ").strip()
            
            if manager.update_hired_status(c['_row'], m_start, m_end):
                print(f"{G}   ✨ UPDATED: Hired{W}")
                manager.delete_response_row(email)
        
        elif choice == '2':
            if manager.update_status_only(c['_row'], "Rejected"):
                print(f"{R}   ❌ UPDATED: Rejected{W}")
                manager.delete_response_row(email)
                
        elif choice == '3':
            return
            
    print(f"\n{B}--- Processing Complete ---{W}")

if __name__ == "__main__":
    main()