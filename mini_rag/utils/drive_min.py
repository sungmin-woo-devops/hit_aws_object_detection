from dotenv import load_dotenv; load_dotenv()

import os, io , mimetypes, pathlib
from typing import Optional, List, Dict

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# ---- 설정 ----
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
ROOT = pathlib.Path(__file__).parent
print("[ROOT]", ROOT)
CRED_PATH = ROOT / "credentials.json"      # 방금 받은 installed 타입
TOKEN_PATH = ROOT / "token.json"           # 최초 발급 후 재사용
FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")   # 선택: 폴더 ID 지정 시 하위 탐색
SHARED_DRIVE_ID = os.getenv("SHARED_DRIVE_ID")  # 공유드라이브면 지정(없으면 None)
OUTDIR = ROOT / "downloads"

def get_creds() -> Credentials:
    creds = None
    
    # credentials.json 파일 존재 확인
    if not CRED_PATH.exists():
        raise FileNotFoundError(
            f"credentials.json 파일이 없습니다. {CRED_PATH}\n"
            "Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 다운로드하세요."
        )
    
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception as e:
            print(f"토큰 파일 읽기 오류: {e}")
            TOKEN_PATH.unlink()  # 손상된 토큰 파일 삭제
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"토큰 갱신 오류: {e}")
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(CRED_PATH), SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                raise Exception(f"OAuth 인증 실패: {e}")
        
        # 토큰 저장
        try:
            with TOKEN_PATH.open("w", encoding="utf-8") as f:
                f.write(creds.to_json())
        except Exception as e:
            print(f"토큰 저장 오류: {e}")
    
    return creds

def build_drive():
    return build("drive", "v3", credentials=get_creds())

# 1) 최상위 최근 파일 10개
def list_recent(svc):
    resp = svc.files().list(
        q="trashed=false",
        pageSize=10,
        fields="files(id,name,mimeType,driveId)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        orderBy="modifiedTime desc"
    ).execute()
    for f in resp.get("files", []):
        print(f"{f['name']}  [{f['id']}]  {f['mimeType']}")

# 2) 특정 폴더 하위 나열(공유드라이브 대응)
def list_children(svc, folder_id: str, drive_id: Optional[str]=None) -> List[Dict]:
    params = dict(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="nextPageToken, files(id,name,mimeType,shortcutDetails,driveId)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        pageSize=1000,
    )
    if drive_id:
        params.update({"corpora":"drive","driveId":drive_id})
    files, token = [], None
    while True:
        if token: params["pageToken"] = token
        try:
            r = svc.files().list(**params).execute()
            files.extend(r.get("files", []))
            token = r.get("nextPageToken")
            if not token: break
        except Exception as e:
            if "Shared drive not found" in str(e):
                print(f"공유 드라이브를 찾을 수 없습니다: {drive_id}")
                print("일반 폴더로 시도합니다...")
                # 공유 드라이브 없이 다시 시도
                params.pop("corpora", None)
                params.pop("driveId", None)
                r = svc.files().list(**params).execute()
                files.extend(r.get("files", []))
                token = r.get("nextPageToken")
                if not token: break
            else:
                raise e
    return files

# 3) 다운로드(구글 문서형은 export, 그 외 바이너리)
def _resolve_shortcut(svc, f):
    if f["mimeType"] == "application/vnd.google-apps.shortcut":
        tid = f["shortcutDetails"]["targetId"]
        return svc.files().get(fileId=tid, fields="id,name,mimeType,parents,driveId",
                               supportsAllDrives=True).execute()
    return f

def download_file(svc, f, outdir: pathlib.Path):
    f = _resolve_shortcut(svc, f)
    outdir.mkdir(parents=True, exist_ok=True)
    name = f["name"].replace("/", "_").strip()
    mt = f["mimeType"]
    # Google Docs류 → PDF export
    export_map = {
        "application/vnd.google-apps.document": "application/pdf",
        "application/vnd.google-apps.spreadsheet": "application/pdf",
        "application/vnd.google-apps.presentation": "application/pdf",
        "application/vnd.google-apps.drawing": "application/pdf",
    }
    if mt in export_map:
        req = svc.files().export_media(fileId=f["id"], mimeType=export_map[mt])
        out = outdir / f"{name}.pdf"
    else:
        req = svc.files().get_media(fileId=f["id"])
        ext = mimetypes.guess_extension(mt) or ""
        out = outdir / (name if name.endswith(ext) else f"{name}{ext}")
    with io.FileIO(out, "wb") as fh:
        dl = MediaIoBaseDownload(fh, req)
        done = False
        while not done:
            _, done = dl.next_chunk()
    print("saved:", out)

if __name__ == "__main__":
    try:
        svc = build_drive()

        print("== 최근 10개 ==")
        list_recent(svc)

        if FOLDER_ID:
            print(f"\n== 폴더 하위({FOLDER_ID}) ==")
            items = list_children(svc, FOLDER_ID, SHARED_DRIVE_ID)
            for f in items[:10]:
                print(f"- {f['name']}  [{f['id']}]  {f['mimeType']}")
            # 예시: 첫 3개만 다운로드
            for f in items[:3]:
                download_file(svc, f, OUTDIR)
    except FileNotFoundError as e:
        print(f"설정 오류: {e}")
        print("\n해결 방법:")
        print("1. Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하세요")
        print("2. credentials.json 파일을 다운로드하여 mini_rag 폴더에 저장하세요")
        print("3. setup_google_drive.md 파일을 참고하세요")
    except Exception as e:
        print(f"오류 발생: {e}")
        print("\n가능한 원인:")
        print("- Google Drive API가 활성화되지 않음")
        print("- OAuth 동의 화면 설정 문제")
        print("- 네트워크 연결 문제")