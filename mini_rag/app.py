# pip install langchain langchain-community langchain-openai google-api-python-client google-auth-httplib2 google-auth-oauthlib faiss-cpu pymupdf python-dotenv
from dotenv import load_dotenv; load_dotenv()

import io, os
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials

# ① PyMuPDF 로더가 추출 정확도 높음
from langchain_community.document_loaders import PyMuPDFLoader  # <- 변경
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_core.prompts import ChatPromptTemplate

ROOT_DIR = Path(__file__).parent
print("[ROOT]", ROOT_DIR)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
creds = Credentials.from_service_account_file("./mini_rag/aws-mini-rag-427a4d162dd2.json", scopes=SCOPES)
drive = build("drive", "v3", credentials=creds)

FOLDER_ID = "1mEb4WtWpO0LeVd3Sgzs4pyQxnt4kbhET"

try:
    folder_meta = drive.files().get(
        fileId=FOLDER_ID,
        fields="id,name,mimeType,driveId,parents"
    ).execute()
    print("[FOLDER]", folder_meta)
except Exception as e:
    raise SystemExit(f"[ERR] 폴더 메타 조회 실패: {e}\n- 서비스계정에 폴더 공유(보기) 권한 부여했는지 확인하세요.")

# 2) 폴더가 Shared Drive면 driveId가 존재합니다.
is_shared_drive = bool(folder_meta.get("driveId"))
params = {
    "q": f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false",
    "fields": "nextPageToken, files(id,name,mimeType,parents)"
}
if is_shared_drive:
    params.update({
        "includeItemsFromAllDrives": True,
        "supportsAllDrives": True,
        "corpora": "drive",
        "driveId": folder_meta["driveId"],
        "pageSize": 1000,
    })
else:
    # My Drive(공유드라이브 아님)이라도 shared-with-me 파일은 접근가능해야 함(폴더 공유 필수)
    params.update({
        "includeItemsFromAllDrives": True,
        "supportsAllDrives": True,
        "pageSize": 1000,
    })

# 3) 페이지네이션 포함 리스트
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
    print(" -", f["id"], f["name"], f.get("mimeType"))

docs = []
for f in files:
    req = drive.files().get_media(fileId=f["id"])
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    tmp_path = ROOT_DIR / f"_tmp_{f['id']}.pdf"
    tmp_path.write_bytes(buf.getvalue())

    # ② 빈 페이지 제거
    pages = PyMuPDFLoader(str(tmp_path)).load()
    pages = [p for p in pages if p.page_content and p.page_content.strip()]
    if not pages:
        print(f"[WARN] 텍스트 미추출(스캔본 가능): {f['name']} (id={f['id']})")
    else:
        for d in pages:
            m = {**d.metadata, "gdrive_name": f["name"], "gdrive_id": f["id"], "gdrive_mtime": f["modifiedTime"]}
            docs.append(Document(page_content=d.page_content, metadata=m))

    tmp_path.unlink(missing_ok=True)

print(f"[INFO] pages kept: {len(docs)}")
assert docs, "모든 파일에서 텍스트를 추출하지 못했습니다. (스캔본이면 OCR 필요)"

splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
chunks = splitter.split_documents(docs)
# ③ 빈 청크 방지
chunks = [c for c in chunks if c.page_content.strip()]
print(f"[INFO] chunks: {len(chunks)}")
assert chunks, "청크가 0건입니다. chunk_size/overlap 조정 또는 OCR 필요"

emb = OpenAIEmbeddings()  # OPENAI_API_KEY는 .env 또는 환경변수
vs = FAISS.from_documents(chunks, emb)
retriever = vs.as_retriever(search_kwargs={"k": 5})

prompt = ChatPromptTemplate.from_messages([
    ("system", "주어진 컨텍스트에 근거해 한국어로 정확히 답변하세요. 모르면 모른다고 하세요."),
    ("human", "질문: {question}\n\n컨텍스트: {context}")
])
llm = ChatOpenAI(model="gpt-4o-mini")
qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type="stuff",
                                 chain_type_kwargs={"prompt": prompt})

print(qa.invoke({"query": "문서 요약 핵심 포인트?"}))
