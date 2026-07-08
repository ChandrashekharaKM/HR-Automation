"""
utils/sheets_helper.py
----------------------
Shared Google Sheets connection helper for SwipeGen HR Automation System.

Eliminates the ~15-line boilerplate connection block that was previously
copy-pasted across all 9 option scripts.
"""
import os
import re
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)

# Default OAuth scopes required by all scripts
_DEFAULT_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def get_client(creds_file: str, scope: list = None) -> gspread.Client:
    """
    Authenticate with Google Sheets using a service account JSON file.

    Args:
        creds_file: Absolute path to service_account.json.
        scope: Optional list of OAuth scopes. Defaults to spreadsheet + drive.

    Returns:
        Authenticated gspread Client.

    Raises:
        FileNotFoundError: If creds_file does not exist.
        Exception: If authentication fails.
    """
    if not os.path.exists(creds_file):
        raise FileNotFoundError(f"Service account file not found: {creds_file}")

    scope = scope or _DEFAULT_SCOPE
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    logger.debug("Authenticated with Google Sheets via service account.")
    return client


def get_worksheet(sheet_url: str, creds_file: str, scope: list = None) -> gspread.Worksheet:
    """
    Connect to a specific Google Sheet tab identified by URL (supports ?gid= tab targeting).

    Args:
        sheet_url: Full Google Sheets URL (may include ?gid=XXXXXXX for tab selection).
        creds_file: Absolute path to service_account.json.
        scope: Optional OAuth scopes.

    Returns:
        The matching gspread Worksheet object.

    Raises:
        ValueError: If sheet_url is empty.
        Exception: If connection fails.
    """
    if not sheet_url:
        raise ValueError("sheet_url must not be empty. Check your .env file.")

    client = get_client(creds_file, scope)
    spreadsheet = client.open_by_url(sheet_url)

    # Extract GID from URL to find the correct tab
    gid_match = re.search(r"gid=([0-9]+)", sheet_url)
    if gid_match:
        target_gid = int(gid_match.group(1))
        for sheet in spreadsheet.worksheets():
            if sheet.id == target_gid:
                logger.info(f"Connected to tab: '{sheet.title}' (gid={target_gid})")
                return sheet
        logger.warning(f"GID {target_gid} not found — falling back to first tab.")

    # Fallback: use the first tab
    fallback = spreadsheet.get_worksheet(0)
    logger.info(f"Connected to first tab: '{fallback.title}'")
    return fallback


def get_two_worksheets(
    primary_url: str,
    secondary_url: str,
    creds_file: str,
    scope: list = None,
):
    """
    Connect to two Google Sheet tabs using a single authenticated client.
    More efficient than calling get_worksheet() twice (one auth round-trip).

    Args:
        primary_url: URL of the primary sheet (e.g. registration sheet).
        secondary_url: URL of the secondary sheet (e.g. interview response sheet).
        creds_file: Absolute path to service_account.json.
        scope: Optional OAuth scopes.

    Returns:
        Tuple (primary_worksheet, secondary_worksheet).
        secondary_worksheet will be None if secondary_url is falsy.
    """
    client = get_client(creds_file, scope)

    def _open(url):
        if not url:
            return None
        spreadsheet = client.open_by_url(url)
        gid_match = re.search(r"gid=([0-9]+)", url)
        if gid_match:
            target_gid = int(gid_match.group(1))
            for sheet in spreadsheet.worksheets():
                if sheet.id == target_gid:
                    logger.info(f"Connected to tab: '{sheet.title}' (gid={target_gid})")
                    return sheet
        fallback = spreadsheet.get_worksheet(0)
        logger.info(f"Connected to first tab: '{fallback.title}'")
        return fallback

    return _open(primary_url), _open(secondary_url)


def find_col_index(headers: list, *keywords, required: bool = False) -> int | None:
    """
    Find a column index (1-based) in a list of header strings by keyword matching.

    Args:
        headers: List of header strings from row_values(1).
        *keywords: One or more lowercase keyword strings to search for.
        required: If True, raises ValueError when column not found.

    Returns:
        1-based column index, or None if not found (when required=False).

    Raises:
        ValueError: If required=True and column not found.
    """
    for i, h in enumerate(headers, 1):
        h_lower = str(h).lower()
        if all(kw in h_lower for kw in keywords):
            return i

    if required:
        raise ValueError(f"Required column not found. Keywords: {keywords}. Headers: {headers}")
    return None


def update_status(worksheet: gspread.Worksheet, row_idx: int, status_value: str) -> bool:
    """
    Update the 'Status' column in a given row.

    Args:
        worksheet: The connected gspread Worksheet.
        row_idx: 1-based row index.
        status_value: The status string to write.

    Returns:
        True on success, False on failure.
    """
    try:
        headers = worksheet.row_values(1)
        col_idx = find_col_index(headers, "status", required=True)
        worksheet.update_cell(row_idx, col_idx, status_value)
        logger.info(f"Row {row_idx} status updated to: '{status_value}'")
        return True
    except Exception as e:
        logger.error(f"Failed to update status for row {row_idx}: {e}")
        return False
