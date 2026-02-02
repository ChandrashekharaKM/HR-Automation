import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

class RecruitmentSummarizer:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(self.base_dir, '..', '.env'))
        self.creds_file = os.path.join(self.base_dir, "service_account.json")
        self.reg_url = os.getenv("REGISTRATION_SHEET_URL") or os.getenv("SHEET_URL")
        self.int_url = os.getenv("INTERVIEW_RESPONSE_SHEET_URL")
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        if not os.path.exists(self.creds_file):
            print(f"{R}❌ Service account file not found: {self.creds_file}{W}")
            
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, self.scope)
        self.client = gspread.authorize(self.creds)

    def get_sheet(self, url):
        try:
            if not url: return None
            spreadsheet = self.client.open_by_url(url)
            gid_match = re.search(r'gid=([0-9]+)', url)
            if gid_match:
                target_gid = int(gid_match.group(1))
                for sheet in spreadsheet.worksheets():
                    if sheet.id == target_gid:
                        return sheet
            return spreadsheet.get_worksheet(0)
        except Exception as e:
            print(f"{R}❌ Connection Error: {e}{W}")
            return None

    def normalize_email(self, email):
        email = str(email).strip().lower()
        if '@' in email:
            username = email.split('@')[0]
            return email, username
        return email, email

    def run_report(self):
        print(f"\n{C}{'='*65}\n📊 RECRUITMENT STATUS SUMMARY & SYNC\n{'='*65}{W}")
        reg_sheet = self.get_sheet(self.reg_url)
        int_sheet = self.get_sheet(self.int_url)

        if not reg_sheet or not int_sheet:
            print(f"{R}❌ Error: One or both sheets could not be reached.{W}")
            return

        reg_records = reg_sheet.get_all_records()
        int_records = int_sheet.get_all_records()

        reg_headers = [h.strip() for h in reg_sheet.row_values(1)]
        email_key = next((h for h in reg_headers if "email" in h.lower()), None)
        try:
            status_col_idx = next((i for i, h in enumerate(reg_headers, 1) if "status" in h.lower()), None)
        except:
            print(f"{R}❌ 'Status' column not found in Registration Sheet.{W}")
            return

        # 1. Map Interview Responses
        interview_map = {} 
        print(f"{Y}📥 Processing interview responses...{W}")
        for row in int_records:
            email = str(row.get('Email address', row.get('Email', ''))).strip().lower()
            avail_key = next((k for k in row.keys() if "available for the interview" in k.lower()), None)
            resp = str(row.get(avail_key, '')).strip() if avail_key else ""
            
            if email and resp:
                full_email, username = self.normalize_email(email)
                interview_map[full_email] = resp
                interview_map[username] = resp

        # Initialize Stats
        stats = {
            'applied': len(reg_records),
            'shortlisted_pool': 0, # Shortlisted + Invited + Accepted
            'not_shortlisted': 0,
            'accepted': 0
        }

        print(f"\n{Y}🔄 Processing registration updates...{W}")
        
        updates_made = 0
        
        for i, row in enumerate(reg_records, start=2):
            email = str(row.get(email_key, '')).strip().lower()
            current_status = str(row.get('Status', '')).strip()

            # Sync Logic
            full_email, username = self.normalize_email(email)
            user_choice = None
            if full_email in interview_map: user_choice = interview_map[full_email]
            elif username in interview_map: user_choice = interview_map[username]
            
            if user_choice:
                user_choice_lower = user_choice.lower()
                target_status = "Interview Accepted" if "yes" in user_choice_lower and "available" in user_choice_lower else "Interview Declined"

                if current_status != target_status:
                    try:
                        reg_sheet.update_cell(i, status_col_idx, target_status)
                        current_status = target_status
                        updates_made += 1
                        print(f"{G}✅ Updated {email} -> {target_status}{W}")
                    except Exception as e:
                        print(f"{R}❌ Failed to update {email}: {e}{W}")

            # --- COUNTING LOGIC ---
            
            # 1. Total Shortlisted (Resume Shortlisted + Invited + Accepted)
            if any(s in current_status for s in ["Resume Shortlisted", "Invited for Interview", "Interview Accepted"]):
                stats['shortlisted_pool'] += 1
            
            # 2. Not Shortlisted
            if "Not Shortlisted" in current_status:
                stats['not_shortlisted'] += 1
            
            # 3. Accepted Count
            if "Interview Accepted" in current_status:
                stats['accepted'] += 1

        print(f"\n{G}✨ Total Updates Made: {updates_made}{W}")
        
        print(f"\n{B}{'='*65}\n📈 FINAL RECRUITMENT REPORT\n{'='*65}{W}")
        print(f"{ 'Total Candidates Applied':<40} | {C}{stats['applied']:<10}{W}")
        print(f"{ 'Total Candidates Shortlisted':<40} | {Y}{stats['shortlisted_pool']:<10}{W}")
        print(f"{ 'Total Candidates Not Shortlisted':<40} | {R}{stats['not_shortlisted']:<10}{W}")
        print(f"{ 'Interview Invites Accepted':<40} | {G}{stats['accepted']:<10}{W}")
        print(f"{B}{'='*65}{W}\n")

def main():
    try:
        summarizer = RecruitmentSummarizer()
        summarizer.run_report()
    except Exception as e:
        print(f"{R}Unexpected Error in Summary Module: {e}{W}")

if __name__ == "__main__":
    main()