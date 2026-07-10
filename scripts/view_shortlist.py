import os
import re
import csv
import requests
from io import StringIO
from dotenv import load_dotenv
from utils.resume_analyser import analyse_resume, print_analysis_report
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load Environment Variables
load_dotenv()
REGISTRATION_SHEET_URL = os.getenv("REGISTRATION_SHEET_URL")
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service_account.json')

# Colors
G, R, Y, B, C, W = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[96m', '\033[0m'

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
        # Fetch metadata to find the sheet name matching the GID
        meta = self.sheet_api.get(spreadsheetId=self.spreadsheet_id).execute()
        for s in meta['sheets']:
            if str(s['properties']['sheetId']) == self.gid:
                print(f"{G}✅ Connected to tab: {s['properties']['title']}{W}")
                return s['properties']['title']
        # Fallback to the first sheet if GID not found
        return meta['sheets'][0]['properties']['title']

    def _get_status_col_letter(self):
        headers = self.sheet_api.values().get(
            spreadsheetId=self.spreadsheet_id, range=f"'{self.sheet_name}'!1:1"
        ).execute().get('values', [[]])[0]
        try:
            idx = headers.index("Status")
        except ValueError:
            idx = 0
        return chr(65 + idx)

    def fetch_pending(self):
        try:
            result = self.sheet_api.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.sheet_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return []
                
            headers = values[0]
            pending_candidates = []
            
            for i, row in enumerate(values[1:]):
                # Google Sheets API might omit trailing empty cells
                padded_row = row + [''] * (len(headers) - len(row))
                row_dict = dict(zip(headers, padded_row))
                
                # Check status
                if not row_dict.get('Status', '').strip():
                    row_dict['_row'] = i + 2
                    pending_candidates.append(row_dict)
                    
            return pending_candidates
        except Exception as e:
            print(f"{R}❌ Error fetching data: {e}{W}")
            return []

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

    # AI-assisted shortlisting default toggle
    ai_default = False
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        resp = input(f"\n👉 {C}Enable AI-assisted shortlisting by default? (y/N): {W}").strip().lower()
        ai_default = (resp == 'y')
    else:
        print(f"{Y}⚠ GEMINI_API_KEY not set — AI analysis disabled.{W}")
    
    print(f"\n{C}{'='*80}\n      OPTION 1: CANDIDATE REGISTRATION & RESUME REVIEW\n{'='*80}{W}")

    while True:
        candidates = manager.fetch_pending()
        if not candidates:
            print(f"\n{G}✅ All pending candidates processed!{W}")
            break

        for c in candidates:
            name = c.get('Name') or c.get('Full Name') or "N/A"
            link = c.get('Resume Link') or c.get('Resume') or "No Link"
            
            print(f"\n{B}SL No. {c['_row']}{W}\t| Name: {Y}{name}{W}\t| Resume: {C}{link}{W}")
            print("-" * 80)
            
            while True:
                print(f"{G}1. Shortlist{W}")
                print(f"{C}A. AI-rate resume (show report){W}")
                print(f"{R}2. Not Shortlist{W}")
                print(f"{Y}3. Break (Main Menu){W}")

                choice = input(f"\n👉 {C}Select option (1/A/2/3): {W}")

                if choice.lower() == 'a':
                    resume_link = c.get('Resume Link') or c.get('Resume')
                    if not resume_link:
                        print(f"{R}No resume link available to analyse.{W}")
                        continue
                    report = analyse_resume(resume_link, SERVICE_ACCOUNT_FILE, os.getenv('GEMINI_API_KEY'))
                    if report:
                        print_analysis_report(report)
                    else:
                        print(f"{R}AI analysis failed or returned no result.{W}")
                    continue

                if choice == '1':
                    # If AI default enabled, run analysis and auto-decision (with confirmation)
                    if ai_default:
                        resume_link = c.get('Resume Link') or c.get('Resume')
                        if resume_link and gemini_key:
                            report = analyse_resume(resume_link, SERVICE_ACCOUNT_FILE, gemini_key)
                            if report:
                                print_analysis_report(report)
                                score = report.get('suitability_score', 0) or 0
                                auto_shortlist = score >= 6
                                if auto_shortlist:
                                    manager.update_sheet(c['_row'], "Resume Shortlisted")
                                    print(f"{G}✅ AI recommended Shortlist (score {score}). Row {c['_row']} updated: Shortlisted{W}")
                                    break
                                else:
                                    manager.update_sheet(c['_row'], "Not Shortlisted")
                                    print(f"{Y}⚠ AI recommended Not Shortlisted (score {score}). Row {c['_row']} updated: Not Shortlisted{W}")
                                    break
                            else:
                                print(f"{R}AI analysis unavailable — please choose manually.{W}")
                                continue
                        else:
                            print(f"{Y}No resume link or GEMINI key — performing manual shortlist.{W}")
                            manager.update_sheet(c['_row'], "Resume Shortlisted")
                            print(f"{G}✅ Row {c['_row']} updated: Shortlisted{W}")
                            break
                    else:
                        manager.update_sheet(c['_row'], "Resume Shortlisted")
                        print(f"{G}✅ Row {c['_row']} updated: Shortlisted{W}")
                        break
                elif choice == '2':
                    manager.update_sheet(c['_row'], "Not Shortlisted")
                    print(f"{R}❌ Row {c['_row']} updated: Rejected{W}")
                    break
                elif choice == '3':
                    print(f"\n{Y}Returning to Main Menu...{W}")
                    return 
                else:
                    print(f"{R}⚠️ Invalid choice.{W}\n")
        
        print(f"\n{B}--- Refreshing Candidate List ---{W}")

if __name__ == "__main__":
    main()