from dotenv import load_dotenv; load_dotenv()
import os, json, time
import gradio as gr
from pathlib import Path
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from app.prompts import RAG_PROMPT
from core.indexer import build_or_load_vectorstore, rebuild_vectorstore
from core.rag import make_qa
from core.vision import analyze_image_or_ocr

# OpenMP 라이브러리 충돌 문제 해결
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

ROOT = Path(__file__).resolve().parents[1]
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")
SHARED_FOLDER_ID = os.getenv("SHARED_FOLDER_ID", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class RagApp:
    def __init__(self):
        self.vs = None
        self.qa = None
        self.k = 5
        self.last_info = ""

    def ensure(self, drive_folder: str = "", shared_folder: str = "", force: bool = False):
        t0 = time.time()
        self.vs = rebuild_vectorstore(drive_folder, shared_folder) \
            if force else build_or_load_vectorstore(drive_folder, shared_folder)
        self.qa = make_qa(self.vs, k=self.k, prompt=RAG_PROMPT, model=OPENAI_MODEL)
        folder_info = f"drive={drive_folder}, shared={shared_folder}" \
            if drive_folder and shared_folder else (drive_folder or shared_folder)
        self.last_info = f"index ready k={self.k} folders={folder_info} ({time.time()-t0:.1f}s)"
        return self.last_info

    def set_k(self, k:int):
        self.k = int(k)
        if self.vs:
            self.qa = make_qa(self.vs, k=self.k, prompt=RAG_PROMPT, model=OPENAI_MODEL)
        return f"k={self.k} 적용"

    def ask(self, msg:str, history):
        if not self.qa: self.ensure(DRIVE_FOLDER_ID, SHARED_FOLDER_ID, force=False)
        resp = self.qa.invoke({"query": msg})
        ans = resp.get("result","").strip()
        srcs = resp.get("source_documents",[]) or []
        lines = []
        for i,d in enumerate(srcs[:3],1):
            m = d.metadata or {}
            lines.append(f"{i}. {m.get('gdrive_name','?')} (id={m.get('gdrive_id','?')}) p.{m.get('page','?')}")
        if lines: ans += "\n\n[참고 문서]\n" + "\n".join(lines)
        return ans

app = RagApp()

with gr.Blocks(title="AWS Diagram RAG") as demo:
    gr.Markdown("### AWS 아키텍처 다이어그램 해설")
    with gr.Row():
        drive_fid = gr.Textbox(value=DRIVE_FOLDER_ID, label="Drive Folder ID", scale=1)
        shared_fid = gr.Textbox(value=SHARED_FOLDER_ID, label="Shared Folder ID", scale=2)
        k_slider = gr.Slider(1,10,value=5,step=1,label="Top-K", scale=1)
    with gr.Row():
        btn_build = gr.Button("인덱스(재)구축")
        stat = gr.Markdown("")

    # RAG 탭
    with gr.Tab("RAG Q&A"):
        chat = gr.Chatbot(type="messages", height=420, label="LLM 해설")
        msg = gr.Textbox(placeholder="예) 데이터 흐름을 설명해줘")
        send = gr.Button("전송", variant="primary")
        clear = gr.Button("대화 지우기")

    # 이미지 해석 탭
    with gr.Tab("이미지 해석"):
        gr.Markdown("""
        ### 📋 사용 방법
        1. **이미지 업로드**: AWS 아키텍처 다이어그램 이미지를 업로드하세요
        2. **OCR 보강**: 이미지에서 텍스트를 자동으로 추출하려면 체크하세요
        3. **아이콘 정보**: AWS 서비스 아이콘과 연결 관계를 JSON으로 입력하세요 (선택사항)
        4. **추가 컨텍스트**: 다이어그램에 대한 추가 설명을 입력하세요 (선택사항)
        5. **이미지 해석**: 버튼을 클릭하여 구조화된 분석 결과를 확인하세요
        """)
        
        img_in = gr.Image(type="pil", label="다이어그램 이미지 업로드")
        use_ocr = gr.Checkbox(value=True, label="OCR 보강")
        
        # 아이콘 탐지 JSON 예시
        icon_json_example = '''{
  "icons": [
    {
      "type": "aws_service",
      "name": "Amazon S3",
      "confidence": 0.95,
      "bbox": [100, 150, 200, 250],
      "description": "Simple Storage Service - 객체 저장소"
    },
    {
      "type": "aws_service", 
      "name": "AWS Lambda",
      "confidence": 0.92,
      "bbox": [300, 200, 400, 300],
      "description": "Serverless compute service - 서버리스 컴퓨팅"
    },
    {
      "type": "aws_service",
      "name": "Amazon CloudFront",
      "confidence": 0.88,
      "bbox": [50, 100, 150, 200],
      "description": "Content Delivery Network - CDN 서비스"
    }
  ],
  "connections": [
    {
      "from": "Amazon CloudFront",
      "to": "Amazon S3",
      "type": "origin",
      "description": "CloudFront가 S3를 오리진으로 사용"
    },
    {
      "from": "Amazon S3",
      "to": "AWS Lambda",
      "type": "trigger",
      "description": "S3 이벤트가 Lambda 함수를 트리거"
    }
  ],
  "metadata": {
    "diagram_type": "architecture",
    "region": "us-east-1",
    "description": "이미지 처리 파이프라인 아키텍처"
  }
}'''
        
        icon_json = gr.Textbox(
            value=icon_json_example,
            label="아이콘 탐지 JSON(선택)", 
            lines=12,
            placeholder="AWS 서비스 아이콘과 연결 관계를 JSON 형태로 입력하세요"
        )
        
        gr.Markdown("""
        **💡 JSON 형식 가이드:**
        - `icons`: AWS 서비스 아이콘 목록
          - `type`: "aws_service" (고정값)
          - `name`: 서비스 이름 (예: "Amazon S3", "AWS Lambda")
          - `confidence`: 신뢰도 (0.0~1.0)
          - `bbox`: [x1, y1, x2, y2] 좌표 (선택사항)
          - `description`: 서비스 설명
        - `connections`: 서비스 간 연결 관계
          - `from`: 출발 서비스명
          - `to`: 도착 서비스명  
          - `type`: 연결 유형 (예: "trigger", "origin", "target")
          - `description`: 연결 설명
        - `metadata`: 다이어그램 메타데이터 (선택사항)
        """)
        
        # 추가 컨텍스트 예시
        extra_ctx_example = '''이 다이어그램은 AWS 서비스를 사용한 이미지 처리 파이프라인을 보여줍니다.

주요 구성 요소:
- 사용자가 이미지를 업로드하면 S3에 저장됩니다
- S3 이벤트가 Lambda 함수를 트리거합니다
- Lambda는 이미지 처리를 수행하고 결과를 다른 S3 버킷에 저장합니다

이 시스템의 목적은 자동화된 이미지 처리 워크플로우를 구현하는 것입니다.

추가 정보:
- 처리 대상: 사용자 업로드 이미지
- 처리 방식: 서버리스 아키텍처
- 확장성: 자동 스케일링 지원'''
        
        extra_ctx = gr.Textbox(
            value=extra_ctx_example,
            label="추가 컨텍스트(선택)", 
            lines=8,
            placeholder="다이어그램에 대한 추가 설명이나 컨텍스트를 입력하세요"
        )
        
        gr.Markdown("""
        **💡 추가 컨텍스트 작성 팁:**
        - 시스템의 목적과 기능을 설명하세요
        - 주요 구성 요소와 역할을 나열하세요
        - 데이터 흐름과 처리 과정을 설명하세요
        - 기술적 특징이나 제약사항을 언급하세요
        - 비즈니스 요구사항이나 사용 사례를 포함하세요
        """)
        
        run_img = gr.Button("이미지 해석", variant="primary")
        out_json = gr.Code(label="구조화 JSON")
        out_expl = gr.Markdown(label="해설")

    def on_build(drive_fid, shared_fid, k):
        try:
            # 폴더 ID 검증
            if not drive_fid and not shared_fid:
                return "❌ Drive Folder ID 또는 Shared Folder ID 중 하나를 입력하세요"
            
            app.set_k(int(k))
            result = app.ensure(drive_fid, shared_fid, force=True)
            return f"✅ {result}"
        except Exception as e:
            error_msg = f"❌ 인덱스 구축 실패: {str(e)}"
            print(error_msg)
            return error_msg

    def on_send(message, history, drive_fid, shared_fid, k):
        if not message: 
            return "", history
        try:
            app.set_k(int(k))
            if not app.qa: 
                app.ensure(drive_fid or DRIVE_FOLDER_ID, shared_fid or SHARED_FOLDER_ID, force=False)
            answer = app.ask(message, history)
            history = history + [
                {"role":"user","content":message},
                {"role":"assistant","content":answer},
            ]
            return "", history
        except Exception as e:
            error_msg = f"❌ 질문 처리 실패: {str(e)}"
            print(error_msg)
            history = history + [
                {"role":"user","content":message},
                {"role":"assistant","content":error_msg},
            ]
            return "", history

    def on_img(img, ocr_flag, icon_json_str, extra):
        raw = analyze_image_or_ocr(img, ocr=ocr_flag, icon_json=icon_json_str, extra_context=extra)
        # JSON 블록 분리 시도
        jtxt, rest = "{}", raw
        try:
            fb = raw.find("{"); lb = raw.rfind("}")
            cand = raw[fb:lb+1] if fb!=-1 and lb!=-1 else "{}"
            jtxt = json.dumps(json.loads(cand), ensure_ascii=False, indent=2)
            rest = raw[lb+1:].strip() if lb+1 < len(raw) else ""
        except: pass
        return jtxt, (rest or "상단의 구조 JSON 확인")

    btn_build.click(on_build, inputs=[drive_fid, shared_fid, k_slider], outputs=[stat])
    k_slider.release(lambda k: app.set_k(int(k)), inputs=[k_slider], outputs=[stat])
    send.click(on_send, inputs=[msg, chat, drive_fid, shared_fid, k_slider], outputs=[msg, chat])
    msg.submit(on_send, inputs=[msg, chat, drive_fid, shared_fid, k_slider], outputs=[msg, chat])
    clear.click(lambda: [], None, chat, queue=False)

if __name__ == "__main__":
    try: app.ensure(DRIVE_FOLDER_ID, SHARED_FOLDER_ID, force=False)
    except Exception as e: print("[init warn]", e)
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)