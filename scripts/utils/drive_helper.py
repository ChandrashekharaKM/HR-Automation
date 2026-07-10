import os
import io
import pickle
import logging
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

def get_drive_service(scripts_dir=None):
    if not scripts_dir:
        # Default to scripts folder in root of project
        scripts_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
    else:
        scripts_dir = Path(scripts_dir)
        
    token_path = scripts_dir / "token.json"
    if not token_path.exists():
        logger.warning(f"token.json not found at {token_path}")
        return None
    try:
        with open(token_path, "rb") as token:
            creds = pickle.load(token)
            
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "wb") as t_out:
                pickle.dump(creds, t_out)
                
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Failed to load drive service: {e}")
        return None

def download_file_from_drive(filename, scripts_dir=None):
    service = get_drive_service(scripts_dir)
    if not service:
        return None
    try:
        q = f"name = '{filename}' and trashed = false"
        results = service.files().list(q=q, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        if not files:
            logger.warning(f"File not found on Google Drive: {filename}")
            return None
            
        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
            
        return fh.getvalue()
    except Exception as e:
        logger.error(f"Error downloading {filename} from Google Drive: {e}")
        return None
