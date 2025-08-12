from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
creds = Credentials.from_service_account_file("./mini_rag/aws-mini-rag-427a4d162dd2.json", scopes=SCOPES)
drive = build("drive", "v3", credentials=creds)

FOLDER_ID = "1mEb4WtWpO0LeVd3Sgzs4pyQxnt4kbhET"  # 제공한 URL의 ID

def resolve_folder_id(fid: str) -> tuple[str, str|None]:
    """바로가기면 targetId로 해소, driveId 반환(Shared Drive 여부 판별)"""
    meta = drive.files().get(
        fileId=fid,
        fields="id,name,mimeType,driveId,shortcutDetails",
        supportsAllDrives=True,
    ).execute()
    if meta.get("mimeType") == "application/vnd.google-apps.shortcut":
        target = meta["shortcutDetails"]["targetId"]
        meta = drive.files().get(
            fileId=target,
            fields="id,name,mimeType,driveId",
            supportsAllDrives=True,
        ).execute()
        fid = meta["id"]
    return fid, meta.get("driveId")

fid, drive_id = resolve_folder_id(FOLDER_ID)
print("[FOLDER_ID]", fid, "driveId=", drive_id)

params = {
    "q": f"'{fid}' in parents and mimeType='application/pdf' and trashed=false",
    "fields": "nextPageToken, files(id,name,mimeType,modifiedTime,parents)",
    "includeItemsFromAllDrives": True,
    "supportsAllDrives": True,
    "pageSize": 1000,
}
if drive_id:  # Shared Drive
    params.update({"corpora": "drive", "driveId": drive_id})

files = []
page_token = None
while True:
    if page_token:
        params["pageToken"] = page_token
    resp = drive.files().list(**params).execute()
    files.extend(resp.get("files", []))
    page_token = resp.get("nextPageToken")
    if not page_token:
        break

print(f"[INFO] PDFs found: {len(files)}")
for f in files:
    print(" -", f["id"], f["name"])
