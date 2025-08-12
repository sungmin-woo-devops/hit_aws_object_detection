# app_gradio.py
# pip install gradio langchain langchain-community langchain-openai google-api-python-client google-auth-httplib2 google-auth-oauthlib faiss-cpu pymupdf python-dotenv

from dotenv import load_dotenv; load_dotenv()
import os, io, json, pathlib, time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import gradio as gr
import PIL.Image as Image

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

# Vision 모듈 import
from core.vision import analyze_image, analyze_image_or_ocr, analyze_aws_architecture

# ========= 기본 설정 =========
ROOT = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CRED_JSON = ROOT / "credentials.json"     # installed 또는 service_account 둘 다 지원
TOKEN_PATH = ROOT / "token.json"
OUTDIR = ROOT / "data" / "raw"
INDEX_DIR = ROOT / "index"                # FAISS 캐시 저장 경로
INDEX_DIR.mkdir(parents=True, exist_ok=True)
OUTDIR.mkdir(parents=True, exist_ok=True)

FOLDER_ID = os.getenv("FOLDER_ID") or "1mEb4WtWpO0LeVd3Sgzs4pyQxnt4kbhET"  # 필요 시 .env로 지정
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ========= 공용 프롬프트 =========
PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     """당신은 AWS 아키텍처 다이어그램 해설 전문가입니다.
다음 규칙에 따라 답변하세요.

1) 역할과 관계: 각 서비스의 역할과 서비스 간 연결/데이터 흐름을 단계별로.
2) 아키텍처 목적 분석: 용도(웹/데이터/마이크로서비스 등), 장점/유의점.
3) 출력 형식:
   - 구성 요소 해설
   - 데이터 흐름
   - 추가 분석(성능/보안/확장성)
4) 제한: 컨텍스트에 없는 정보는 "제공된 정보로는 확인 불가"라고 명시.
불필요한 서론 없이 핵심부터 제시.
"""),
    ("human", "질문: {question}\n\n컨텍스트: {context}")
])

# ========= 자격 로더 (installed / service_account 자동 분기) =========
def load_creds_auto(json_path: pathlib.Path, scopes) -> object:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    t = data.get("type")
    if t == "service_account":
        return SvcCreds.from_service_account_file(str(json_path), scopes=scopes)
    if "installed" in data or "web" in data:
        creds = None
        if TOKEN_PATH.exists():
            creds = UserCreds.from_authorized_user_file(str(TOKEN_PATH), scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(json_path), scopes)
                creds = flow.run_local_server(port=0)
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        return creds
    raise ValueError("지원되지 않는 credentials.json 형식입니다.")

def build_drive():
    creds = load_creds_auto(CRED_JSON, SCOPES)
    return build("drive", "v3", credentials=creds)

# ========= 인덱싱 파이프라인 =========
def fetch_pdfs_from_drive(folder_id: str) -> List[Dict]:
    drive = build_drive()
    # 폴더 메타
    meta = drive.files().get(fileId=folder_id, fields="id,name,mimeType,driveId").execute()
    is_shared = bool(meta.get("driveId"))
    params = {
        "q": f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false",
        "fields": "nextPageToken, files(id,name,mimeType,parents,modifiedTime)",
        "includeItemsFromAllDrives": True,
        "supportsAllDrives": True,
        "pageSize": 1000,
    }
    if is_shared:
        params.update({"corpora": "drive", "driveId": meta["driveId"]})

    files, token = [], None
    while True:
        if token: params["pageToken"] = token
        r = drive.files().list(**params).execute()
        files.extend(r.get("files", []))
        token = r.get("nextPageToken")
        if not token: break
    return files

def download_pdf(file_id: str, filename: str) -> pathlib.Path:
    drive = build_drive()
    outpath = OUTDIR / filename
    if outpath.exists():
        return outpath
    
    request = drive.files().get_media(fileId=file_id)
    with open(outpath, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    return outpath

def process_pdf(pdf_path: pathlib.Path) -> List[Document]:
    loader = PyMuPDFLoader(str(pdf_path))
    pages = loader.load()
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_documents(pages)

def build_or_load_vectorstore(folder_id: str) -> Tuple[FAISS, int]:
    index_path = INDEX_DIR / f"faiss_{folder_id}"
    
    if index_path.exists():
        print(f"기존 인덱스 로드: {index_path}")
        embeddings = OpenAIEmbeddings()
        vs = FAISS.load_local(str(index_path), embeddings)
        return vs, len(vs.docstore._dict)
    
    print(f"새 인덱스 구축: {folder_id}")
    files = fetch_pdfs_from_drive(folder_id)
    if not files:
        raise ValueError(f"폴더 {folder_id}에서 PDF를 찾을 수 없습니다.")
    
    all_docs = []
    for f in files:
        try:
            pdf_path = download_pdf(f["id"], f["name"])
            docs = process_pdf(pdf_path)
            for doc in docs:
                doc.metadata.update({
                    "gdrive_id": f["id"],
                    "gdrive_name": f["name"],
                    "modified": f.get("modifiedTime", "")
                })
            all_docs.extend(docs)
            print(f"처리 완료: {f['name']} ({len(docs)} chunks)")
        except Exception as e:
            print(f"오류 {f['name']}: {e}")
    
    if not all_docs:
        raise ValueError("처리할 문서가 없습니다.")
    
    embeddings = OpenAIEmbeddings()
    vs = FAISS.from_documents(all_docs, embeddings)
    vs.save_local(str(index_path))
    print(f"인덱스 저장: {index_path}")
    return vs, len(all_docs)

def make_qa(vs: FAISS, k: int) -> RetrievalQA:
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vs.as_retriever(search_kwargs={"k": k}),
        chain_type="stuff",
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True
    )
    return qa

# ========= 이미지 분석 함수 =========
def analyze_uploaded_image(image, use_ocr=False, extra_context="", analysis_type="standard", icon_json=""):
    """업로드된 이미지를 분석하는 함수"""
    if image is None:
        return "이미지를 업로드해주세요."
    
    try:
        # PIL Image로 변환
        if hasattr(image, 'convert'):
            pil_img = image
        else:
            pil_img = Image.fromarray(image)
        
        # 분석 타입에 따른 처리
        if analysis_type == "aws_architecture":
            result = analyze_aws_architecture(pil_img, detailed=True, include_recommendations=True)
        elif use_ocr:
            result = analyze_image_or_ocr(pil_img, ocr=True, extra_context=extra_context, icon_json=icon_json)
        else:
            result = analyze_image(pil_img, extra_context=extra_context, icon_json=icon_json)
        
        return result
    except Exception as e:
        return f"이미지 분석 중 오류가 발생했습니다: {str(e)}"

# ========= Gradio 핸들러 =========
class RagApp:
    def __init__(self):
        self.vs: Optional[FAISS] = None
        self.qa: Optional[RetrievalQA] = None
        self.k: int = 5
        self.last_build_info = ""

    def ensure_index(self, folder_id: str, force: bool = False) -> str:
        if force or self.vs is None:
            t0 = time.time()
            self.vs, n = build_or_load_vectorstore(folder_id)
            self.qa = make_qa(self.vs, self.k)
            self.last_build_info = f"인덱스 준비 완료 (k={self.k}, chunks={n}, folder={folder_id}, {time.time()-t0:.1f}s)"
        elif self.qa is None:
            self.qa = make_qa(self.vs, self.k)
        return self.last_build_info

    def set_k(self, k: int) -> str:
        self.k = int(k)
        if self.vs:
            self.qa = make_qa(self.vs, self.k)
        return f"k={self.k} 설정 완료"

    def ask(self, message: str, history: List[List[str]]) -> str:
        if not self.qa:
            self.ensure_index(FOLDER_ID, force=False)
        resp = self.qa.invoke({"query": message})
        answer = resp.get("result", "").strip()
        sources = resp.get("source_documents", []) or []
        # 소스 3개까지 표기
        src_lines = []
        for i, d in enumerate(sources[:3], 1):
            m = d.metadata or {}
            src_lines.append(f"{i}. {m.get('gdrive_name','?')} (id={m.get('gdrive_id','?')}) p.{m.get('page', '?')}")
        if src_lines:
            answer += "\n\n[참고 문서]\n" + "\n".join(src_lines)
        return answer

app = RagApp()

# ========= Gradio UI =========
with gr.Blocks(title="AWS Diagram RAG & Vision") as demo:
    gr.Markdown("### AWS 아키텍처 다이어그램 해설 RAG & Vision")
    
    with gr.Tabs():
        # RAG 탭
        with gr.TabItem("📚 문서 기반 RAG"):
            with gr.Row():
                folder_in = gr.Textbox(value=FOLDER_ID, label="Google Drive Folder ID")
                k_slider = gr.Slider(1, 10, value=5, step=1, label="Top-K(검색 문서 수)")
            with gr.Row():
                btn_build = gr.Button("인덱스(재)구축 / 로드")
                build_status = gr.Markdown("")
            chat = gr.Chatbot(height=420, label="LLM 해설", type="messages")
            msg = gr.Textbox(placeholder="질문을 입력하세요. 예) 이 다이어그램의 데이터 흐름을 설명해줘", label="질문")
            with gr.Row():
                send_btn = gr.Button("전송", variant="primary")
                clear_btn = gr.Button("대화 지우기")

        # Vision 탭
        with gr.TabItem("🖼️ 이미지 분석"):
            with gr.Row():
                with gr.Column(scale=1):
                    image_input = gr.Image(label="AWS 다이어그램 업로드", type="pil")
                    with gr.Row():
                        analysis_type = gr.Radio(
                            choices=["standard", "aws_architecture"], 
                            value="aws_architecture",
                            label="분석 타입",
                            info="AWS 아키텍처: 전문적 분석, Standard: 기본 분석"
                        )
                        ocr_checkbox = gr.Checkbox(label="OCR 사용", value=False)
                    analyze_btn = gr.Button("이미지 분석", variant="primary")
                    extra_context = gr.Textbox(
                        label="추가 컨텍스트 (선택사항)", 
                        placeholder="추가적인 정보나 특별한 요구사항이 있다면 입력하세요",
                        lines=3
                    )
                    icon_json = gr.Textbox(
                        label="아이콘 탐지 JSON (선택사항)", 
                        placeholder="아이콘 탐지 결과 JSON을 입력하세요",
                        lines=3
                    )
                with gr.Column(scale=1):
                    analysis_output = gr.Textbox(
                        label="분석 결과", 
                        lines=20, 
                        max_lines=30,
                        interactive=False
                    )

    def on_build(fid, k):
        app.set_k(int(k))
        return app.ensure_index(fid, force=True)

    def on_send(message, history, fid, k):
        # history: [{"role":"user","content":"..."}, {"role":"assistant","content":"..."} ...]
        if not message:
            return gr.update(), history
        if not app.qa:
            app.set_k(int(k))
            app.ensure_index(fid, force=False)

        answer = app.ask(message, history)
        # 메시지 두 개 append (user, assistant)
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": answer},
        ]
        return "", history

    def on_k_change(k):
        return app.set_k(int(k))

    def on_analyze_image(image, use_ocr, context, analysis_type, icon_json):
        return analyze_uploaded_image(image, use_ocr, context, analysis_type, icon_json)
    
    def on_image_upload(image):
        """이미지 업로드 시 텍스트박스 초기화"""
        if image is not None:
            return gr.update(value=""), gr.update(value="")  # extra_context, icon_json 초기화
        return gr.update(), gr.update()

    # RAG 탭 이벤트
    btn_build.click(on_build, inputs=[folder_in, k_slider], outputs=[build_status])
    k_slider.release(on_k_change, inputs=[k_slider], outputs=[build_status])
    send_btn.click(on_send, inputs=[msg, chat, folder_in, k_slider], outputs=[msg, chat])
    msg.submit(on_send, inputs=[msg, chat, folder_in, k_slider], outputs=[msg, chat])
    clear_btn.click(lambda: [], None, chat, queue=False)
    
    # Vision 탭 이벤트
    analyze_btn.click(
        on_analyze_image, 
        inputs=[image_input, ocr_checkbox, extra_context, analysis_type, icon_json], 
        outputs=[analysis_output]
    )
    
    # 이미지 업로드 시 텍스트박스 초기화
    image_input.change(
        on_image_upload,
        inputs=[image_input],
        outputs=[extra_context, icon_json]
    )

if __name__ == "__main__":
    # 최초 한 번 로드 시도(캐시가 있으면 바로 로드)
    try:
        app.ensure_index(FOLDER_ID, force=False)
    except Exception as e:
        print("[WARN] 인덱스 초기 로드 실패:", e)
    demo.launch(server_name="0.0.0.0", server_port=7860)
