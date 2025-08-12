from dotenv import load_dotenv; load_dotenv()

import json
from pathlib import Path
from google.oauth2.credentials import Credentials as UserCreds
from google.oauth2.service_account import Credentials as SvcCreds
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def load_creds_auto(json_path: Path, scopes, token_path: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    t = data.get("type")
    if t == "service_account":
        return SvcCreds.from_service_account_file(str(json_path), scopes=scopes)
    if "installed" in data or "web" in data:
        creds = None
        if token_path.exists():
            creds = UserCreds.from_authorized_user_file(str(token_path), scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(json_path), scopes)
                creds = flow.run_local_server(port=0)
            token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds
    raise ValueError("지원되지 않는 credentials.json 형식")