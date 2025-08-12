from dotenv import load_dotenv; load_dotenv()

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pathlib import Path
import io
from typing import List, Dict
from langchain_core.documents import Document

def build_drive(creds):
    return build("drive", "v3", credentials=creds)

def list_pdfs(drive, folder_id: str, folder_type: str = "drive") -> tuple[List[Dict], bool]:
    # 폴더 ID가 비어있는지 확인
    if not folder_id or folder_id.strip() == "":
        print(f"⚠️ {folder_type} 폴더 ID가 설정되지 않았습니다")
        return [], False
    
    try:
        # Google Drive API v3의 올바른 필드명 사용
        meta = drive.files().get(fileId=folder_id, fields="id,name,mimeType,driveId").execute()
        is_shared = bool(meta.get("driveId"))
        print(f"✅ {folder_type} 폴더 정보 조회 성공: {meta.get('name', 'Unknown')}")
    except Exception as e:
        print(f"⚠️ {folder_type} 폴더 정보 조회 실패: {e}")
        # 기본값으로 설정
        is_shared = False
    
    # Google Drive API v3의 올바른 필드명 사용
    params = {
        "q": f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false",
        "fields": "nextPageToken, files(id,name,mimeType,parents,modifiedTime)",
        "includeItemsFromAllDrives": True, 
        "supportsAllDrives": True, 
        "pageSize": 1000
    }
    
    if is_shared and meta.get("driveId"):
        params.update({"corpora":"drive","driveId":meta["driveId"]})
    
    files, token = [], None
    while True:
        if token: 
            params["pageToken"] = token
        try:
            r = drive.files().list(**params).execute()
            files.extend(r.get("files", []))
            token = r.get("nextPageToken")
            if not token: 
                break
        except Exception as e:
            print(f"⚠️ {folder_type} 파일 목록 조회 실패: {e}")
            break
    
    print(f"📁 {folder_type}에서 발견된 PDF 파일: {len(files)}개")
    return files, is_shared

def download_pdfs_to_docs(drive, files: List[Dict], tmp_dir: Path) -> List[Document]:
    from langchain_community.document_loaders import PyMuPDFLoader
    docs = []
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📥 {len(files)}개의 PDF 파일을 다운로드하고 처리합니다...")
    
    for i, f in enumerate(files, 1):
        try:
            print(f"  📄 [{i}/{len(files)}] {f['name']} 처리 중...")
            
            req = drive.files().get_media(fileId=f["id"])
            buf = io.BytesIO()
            dl = MediaIoBaseDownload(buf, req)
            done = False
            while not done: 
                _, done = dl.next_chunk()
            
            pdf = tmp_dir / f"_tmp_{f['id']}.pdf"
            pdf.write_bytes(buf.getvalue())
            
            # PDF 로드 및 텍스트 추출
            try:
                pages = PyMuPDFLoader(str(pdf)).load()
                page_count = 0
                for d in pages:
                    if d.page_content and d.page_content.strip():
                        m = {
                            **d.metadata, 
                            "gdrive_name": f["name"], 
                            "gdrive_id": f["id"], 
                            "gdrive_mtime": f["modifiedTime"]
                        }
                        docs.append(Document(page_content=d.page_content.strip(), metadata=m))
                        page_count += 1
                
                print(f"    ✅ {page_count}페이지 텍스트 추출 완료")
                
            except Exception as e:
                print(f"    ⚠️ PDF 처리 실패: {e}")
                continue
            finally:
                pdf.unlink(missing_ok=True)
                
        except Exception as e:
            print(f"    ❌ 파일 다운로드 실패: {e}")
            continue
    
    print(f"📚 총 {len(docs)}개의 문서 청크를 생성했습니다")
    return docs
