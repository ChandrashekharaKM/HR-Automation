import os
import re
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

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
            
            # Connect to Sheet 1 (Registration)
            self.worksheet = self._get_sheet_by_url(client, self.sheet_url)
            
            # Connect to Sheet 2 (Responses)
            if self.response_url:
                self.resp_sheet = self._get_sheet_by_url(client, self.response_url)
            
            if not self.worksheet: return False
            return True
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}"); return False

    def get_confirmed_emails(self):
        """Fetches emails from Sheet 2 where answer matches 'Yes, I am available.'"""
        if not self.resp_sheet: return set()
        try:
            print(f"{Y}⏳ Checking Sheet 2 for 'Yes' responses...{W}")
            responses = self.resp_sheet.get_all_records()
            yes_emails = set()
            
            for row in responses:
                # Find the availability column (fuzzy match)
                avail_key = next((k for k in row.keys() if "available" in k.lower()), None)
                email = str(row.get('Email address', row.get('Email', ''))).strip().lower()
                
                if avail_key:
                    answer = str(row[avail_key]).strip().lower()
                    if "yes" in answer:
                        yes_emails.add(email)
            
            print(f"{G}   Found {len(yes_emails)} candidates who said 'Yes'.{W}")
            return yes_emails
        except Exception as e:
            print(f"{R}❌ Error reading Sheet 2: {e}{W}")
            return set()

    def fetch_processable_candidates(self, yes_emails):
        """
        Fetches candidates from Sheet 1 WHO:
        1. Are in the 'Yes' list (Sheet 2)
        2. Status matches 'Interview Accepted'
        """
        try:
            data = self.worksheet.get_all_values()
            if not data: return []
            
            headers = [h.strip() if h.strip() else f"col_{i}" for i, h in enumerate(data[0])]
            candidates = []
            
            print(f"{Y}⏳ Matching with Sheet 1 candidates...{W}")

            for i, row in enumerate(data[1:], 1):
                row_dict = dict(zip(headers, row))
                email = str(row_dict.get('Email address', row_dict.get('Email', ''))).strip().lower()
                status = str(row_dict.get('Status', '')).strip().lower()

                # LOGIC: 
                # 1. Email must be in the "Yes" list
                # 2. Status must match "Interview Accepted"
                is_accepted = "interview accepted" in status
                has_said_yes = email in yes_emails

                if has_said_yes and is_accepted:
                    row_dict['_row'] = i + 1
                    candidates.append(row_dict)
                
            return candidates
        except Exception as e:
            print(f"{R}❌ Error fetching data: {e}{W}"); return []

    def update_hired_status(self, row_idx, start_date, end_date):
        try:
            headers = self.worksheet.row_values(1)
            
            # Find Columns Dynamically
            try:
                status_col = next(i for i, h in enumerate(headers, 1) if "status" in h.lower())
                start_col = next(i for i, h in enumerate(headers, 1) if "start" in h.lower() and "date" in h.lower())
                end_col = next(i for i, h in enumerate(headers, 1) if "end" in h.lower() and "date" in h.lower())
            except StopIteration:
                print(f"{R}❌ Error: 'Start_Date' or 'End_Date' columns missing in Sheet 1.{W}")
                return False

            self.worksheet.update_cell(row_idx, status_col, "Hired")
            self.worksheet.update_cell(row_idx, start_col, start_date)
            self.worksheet.update_cell(row_idx, end_col, end_date)
            return True
        except Exception as e:
            print(f"{R}❌ Update error: {e}{W}")
            return False

    def update_status_only(self, row_idx, status):
        try:
            headers = self.worksheet.row_values(1)
            status_col = next(i for i, h in enumerate(headers, 1) if "status" in h.lower())
            self.worksheet.update_cell(row_idx, status_col, status)
            return True
        except: return False

def main():
    manager = HiringManager()
    if not manager.connect(): return
    
    # 1. Identify who said "Yes" in Sheet 2
    yes_emails = manager.get_confirmed_emails()
    if not yes_emails:
        print(f"\n{Y}⚠️  No candidates have replied 'Yes' in Sheet 2 yet.{W}"); return

    # 2. Filter Sheet 1 for 'Interview Accepted'
    candidates = manager.fetch_processable_candidates(yes_emails)
    
    if not candidates:
        print(f"\n{G}✅ No pending 'Interview Accepted' candidates who confirmed 'Yes'.{W}")
        return

    # 3. Loop through them
    print(f"\n{B}--- Processing {len(candidates)} Candidates (Accepted & Available) ---{W}")
    
    for c in candidates:
        name = c.get('Name') or c.get('Full Name') or "N/A"
        email = c.get('Email address') or c.get('Email') or "N/A"
        
        # Try to find existing start date to suggest
        auto_start = c.get('Expected Start Date') or c.get('Start Date') or datetime.now().strftime("%d-%m-%Y")

        print(f"\n{B}Candidate: {Y}{name}{W} | {email}")
        print(f"Status: {C}Interview Accepted -> Said YES{W}")
        print("-" * 50)
        print(f"{G}1. Hired{W}")
        print(f"{R}2. Reject{W}")
        print(f"{Y}3. Exit{W}")
        
        choice = input(f"👉 Decision: ").strip()
        
        if choice == '1':
            print(f"   Suggested Start: {Y}{auto_start}{W}")
            use_auto = input("   Use suggested date? (y/n): ").strip().lower()
            
            if use_auto == 'y':
                m_start = auto_start
            else:
                m_start = input(f"   🗓️  Enter Start Date ({Y}DD-MM-YYYY{W}): ").strip()
            
            m_end = input(f"   🏁 Enter End Date ({Y}DD-MM-YYYY{W}): ").strip()
            
            if manager.update_hired_status(c['_row'], m_start, m_end):
                print(f"{G}   ✨ UPDATED: Hired{W}")
        
        elif choice == '2':
            if manager.update_status_only(c['_row'], "Rejected"):
                print(f"{R}   ❌ UPDATED: Rejected{W}")
                
        elif choice == '3':
            return
            
    print(f"\n{B}--- All Pending Candidates Processed ---{W}")

if __name__ == "__main__":
    main()