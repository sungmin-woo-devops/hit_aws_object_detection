import os, json
from pathlib import Path
from typing import Tuple
from dotenv import load_dotenv; load_dotenv()
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from core.drive_auth import load_creds_auto
from core.drive_io import build_drive, list_pdfs, download_pdfs_to_docs

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "data" / "raw"
INDEX_DIR = ROOT / "index"
CRED = ROOT / "credentials.json"
TOKEN = ROOT / "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def _check_gpu_availability() -> bool:
    """GPU 사용 가능 여부를 확인합니다."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def _load_emb():
    """GPU가 있으면 GPU를 사용하는 OpenAI Embeddings를 로드합니다."""
    gpu_available = _check_gpu_availability()
    
    if gpu_available:
        print("🚀 GPU 감지됨 - GPU 가속을 사용합니다")
        # GPU 메모리 최적화를 위한 설정
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        return OpenAIEmbeddings(
            model="text-embedding-3-small",  # GPU에서 더 효율적인 모델
            dimensions=1536
        )
    else:
        print("💻 CPU 모드로 실행합니다")
        return OpenAIEmbeddings()

def _index_paths():
    idx = INDEX_DIR / "faiss_idx"; meta = INDEX_DIR / "faiss_meta.json"
    idx.mkdir(parents=True, exist_ok=True)
    return idx, meta

def build_or_load_vectorstore(drive_folder: str = "", shared_folder: str = "") -> FAISS:
    emb = _load_emb()
    idx, meta = _index_paths()
    
    # 폴더 ID 조합으로 캐시 키 생성
    cache_key = f"{drive_folder}_{shared_folder}"
    
    if (idx / "index.faiss").exists() and meta.exists():
        m = json.loads(meta.read_text(encoding="utf-8"))
        if m.get("cache_key") == cache_key:
            return FAISS.load_local(str(idx), emb, allow_dangerous_deserialization=True)
    return rebuild_vectorstore(drive_folder, shared_folder)

def rebuild_vectorstore(drive_folder: str = "", shared_folder: str = "") -> FAISS:
    print(f"🔄 벡터스토어 재구성을 시작합니다...")
    print(f"   📁 Drive 폴더: {drive_folder or '설정되지 않음'}")
    print(f"   📁 Shared 폴더: {shared_folder or '설정되지 않음'}")
    
    # 폴더 ID 검증
    if not drive_folder and not shared_folder:
        raise RuntimeError("Google Drive 폴더 ID가 설정되지 않았습니다. .env 파일에서 DRIVE_FOLDER 또는 SHARED_FOLDER를 설정하세요.")
    
    try:
        creds = load_creds_auto(CRED, SCOPES, TOKEN)
        drive = build_drive(creds)
        print("✅ Google Drive API 연결 성공")
        
        all_files = []
        all_docs = []
        
        # Drive 폴더 처리
        if drive_folder:
            files, _ = list_pdfs(drive, drive_folder, "Drive")
            if files:
                all_files.extend(files)
                docs = download_pdfs_to_docs(drive, files, OUTDIR)
                all_docs.extend(docs)
        
        # Shared 폴더 처리
        if shared_folder:
            files, _ = list_pdfs(drive, shared_folder, "Shared")
            if files:
                all_files.extend(files)
                docs = download_pdfs_to_docs(drive, files, OUTDIR)
                all_docs.extend(docs)
        
        if not all_files:
            raise RuntimeError("설정된 폴더에서 PDF 파일을 찾을 수 없습니다. 폴더 ID를 확인하거나 폴더에 PDF 파일이 있는지 확인하세요.")
        
        if not all_docs:
            raise RuntimeError("PDF에서 텍스트를 추출할 수 없습니다. 파일이 손상되었거나 텍스트가 없을 수 있습니다")
        
        print(f"📝 {len(all_docs)}개의 문서를 청킹합니다...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
        chunks = [c for c in splitter.split_documents(all_docs) if c.page_content.strip()]
        
        if not chunks: 
            raise RuntimeError("청크 0건 → PDF에 텍스트가 없거나 OCR이 필요할 수 있습니다")
        
        print(f"📄 {len(chunks)}개의 청크를 임베딩합니다...")
        emb = _load_emb()
        vs = FAISS.from_documents(chunks, emb)
        
        idx, meta = _index_paths()
        vs.save_local(str(idx))
        
        # 캐시 키 생성
        cache_key = f"{drive_folder}_{shared_folder}"
        meta.write_text(json.dumps({
            "cache_key": cache_key,
            "drive_folder": drive_folder,
            "shared_folder": shared_folder,
            "doc_count": len(chunks)
        }), encoding="utf-8")
        
        print(f"✅ 벡터스토어가 저장되었습니다: {len(chunks)}개 청크")
        return vs
        
    except Exception as e:
        print(f"❌ 벡터스토어 재구성 실패: {e}")
        raise
