from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
ROOT_DIR = Path(__file__).parent

flow = InstalledAppFlow.from_client_secrets_file(ROOT_DIR / "credentials.json", SCOPES)
creds = flow.run_local_server(port=0)   # 브라우저 뜸 (오프라인 토큰 발금)

with open("token.json", "w") as token:
    token.write(creds.to_json())

print("Token saved to token.json")
