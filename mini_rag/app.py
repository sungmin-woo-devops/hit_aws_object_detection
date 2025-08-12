# pip install langchain langchain-community langchain-openai google-api-python-client google-auth-httplib2 google-auth-oauthlib faiss-cpu pymupdf python-dotenv
from dotenv import load_dotenv; load_dotenv()
import io, os, pathlib
from pathlib import Path
from typing import List, Dict, Optional

import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials as UserCreds
from google.oauth2.service_account import Credentials as SvcCreds
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_core.prompts import ChatPromptTemplate

def load_creds_auto(json_path: pathlib.Path, scopes):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    t = data.get("type")
    if t == "service_account":
        return SvcCreds.from_service_account_file(str(json_path), scopes=scopes)
    if "installed" in data or "web" in data:
        # OAuth 데스크톱/웹 클라이언트
        token = json_path.parent / "token.json"
        creds = None
        if token.exists():
            creds = UserCreds.from_authorized_user_file(str(token), scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # 'installed' or 'web' 모두 from_client_secrets_file 가능
                flow = InstalledAppFlow.from_client_secrets_file(str(json_path), scopes)
                creds = flow.run_local_server(port=0)
            token.write_text(creds.to_json(), encoding="utf-8")
        return creds
    raise ValueError("지원되지 않는 자격 파일 형식입니다.")


# ===== 설정 =====
ROOT_DIR = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS = load_creds_auto(ROOT_DIR / "credentials.json", SCOPES)
DRIVE = build("drive", "v3", credentials=CREDENTIALS)
OUTDIR = ROOT_DIR / "data/raw"

DRIVE_FOLDER = os.getenv("DRIVE_FOLDER", "")
SHARED_FOLDER = os.getenv("SHARED_FOLDER", "")


# ===== 폴더 메타 조회 =====
try:
    folder_meta = DRIVE.files().get(
        fileId=FOLDER_ID,
        fields="id,name,mimeType,driveId,parents"
    ).execute()
except Exception as e:
    raise SystemExit(f"[ERR] 폴더 메타 조회 실패: {e}")

is_shared_drive = bool(folder_meta.get("driveId"))
params = {
    "q": f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false",
    "fields": "nextPageToken, files(id,name,mimeType,parents,modifiedTime)",
    "includeItemsFromAllDrives": True,
    "supportsAllDrives": True,
    "pageSize": 1000,
}
if is_shared_drive:
    params.update({"corpora": "drive", "driveId": folder_meta["driveId"]})

# ===== 파일 목록 =====
files, token = [], None
while True:
    if token:
        params["pageToken"] = token
    resp = DRIVE.files().list(**params).execute()
    files.extend(resp.get("files", []))
    token = resp.get("nextPageToken")
    if not token:
        break

print(f"[INFO] PDFs found: {len(files)}")
docs = []
for f in files:
    req = DRIVE.files().get_media(fileId=f["id"])
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    tmp_path = ROOT_DIR / f"_tmp_{f['id']}.pdf"
    tmp_path.write_bytes(buf.getvalue())

    pages = PyMuPDFLoader(str(tmp_path)).load()
    pages = [p for p in pages if p.page_content.strip()]
    for d in pages:
        m = {**d.metadata, "gdrive_name": f["name"], "gdrive_id": f["id"], "gdrive_mtime": f["modifiedTime"]}
        docs.append(Document(page_content=d.page_content, metadata=m))
    tmp_path.unlink(missing_ok=True)

# ===== 청크 나누기 =====
splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
chunks = [c for c in splitter.split_documents(docs) if c.page_content.strip()]

# ===== FAISS 인덱스 생성 =====
emb = OpenAIEmbeddings()
vs = FAISS.from_documents(chunks, emb)
retriever = vs.as_retriever(search_kwargs={"k": 5})

prompt = ChatPromptTemplate.from_messages([
    ("system",
        """당신은 AWS 아키텍처 다이어그램 해설 전문가입니다.
다음 규칙에 따라 답변하세요.

1. **역할과 관계 설명**  
   - 각 AWS 서비스 아이콘이 수행하는 역할을 간단히 설명합니다.  
   - 서비스 간 연결 관계와 데이터 흐름을 단계별로 해설합니다.

2. **아키텍처 목적 분석**  
   - 다이어그램의 주요 목적(예: 웹 서비스, 데이터 파이프라인, 마이크로서비스 등)을 추론합니다.  
   - 해당 구성의 장점과 고려해야 할 점을 제시합니다.

3. **출력 형식**  
   - `구성 요소 해설` → 서비스별 기능 설명  
   - `데이터 흐름` → 단계별 흐름 설명  
   - `추가 분석` → 성능, 보안, 확장성 관점의 코멘트

4. **제한 사항**  
   - 컨텍스트에 없는 정보는 추측하지 않고 "제공된 정보로는 확인 불가"라고 말합니다.  
   - 불필요한 서론 없이 핵심 내용부터 전달합니다.
"""),
    ("human", "질문: {question}\n\n컨텍스트: {context}")
])
llm = ChatOpenAI(model="gpt-4o-mini")
qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff",
                                 chain_type_kwargs={"prompt": prompt})

print(qa.invoke({"query": "문서 요약 핵심 포인트?"}))
