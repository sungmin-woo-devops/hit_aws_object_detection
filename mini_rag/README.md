# Mini RAG - AWS 다이어그램 분석 시스템

AWS 아키텍처 다이어그램을 분석하고 질의응답을 제공하는 RAG(Retrieval-Augmented Generation) 시스템입니다.

## 주요 기능

### 📄 문서 기반 RAG
- Google Drive에서 PDF 문서 자동 수집
- FAISS 벡터 데이터베이스로 문서 인덱싱
- LangChain 기반 질의응답 시스템

### 🖼️ Vision AI 분석
- OpenAI Vision API를 활용한 이미지 분석
- AWS 아키텍처 다이어그램 전문 분석
- OCR 기능으로 텍스트 추출 지원

### 🎨 Gradio 웹 인터페이스
- 직관적인 웹 UI 제공
- 실시간 이미지 업로드 및 분석
- 문서 검색 및 질의응답

## 설치 및 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일 생성:
```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
FOLDER_ID=your_google_drive_folder_id
```

### 3. Google Drive 인증
- `credentials.json` 파일을 프로젝트 루트에 배치
- OAuth 2.0 또는 서비스 계정 인증 지원

## 사용법

### Vision 전용 앱 (권장)
```bash
python run_vision_app.py
```

### 전체 RAG + Vision 앱
```bash
python gradio_app.py
```

### 프로그래밍 방식
```python
from core.vision import analyze_aws_architecture
import PIL.Image as Image

image = Image.open("aws_diagram.png")
result = analyze_aws_architecture(image)
```

## 프로젝트 구조

```
mini_rag/
├── app.py              # 기본 RAG 애플리케이션
├── gradio_app.py       # Gradio 웹 인터페이스
├── run_vision_app.py   # Vision 전용 앱
├── core/               # 핵심 모듈
│   ├── vision.py       # Vision AI 분석
│   ├── rag.py          # RAG 파이프라인
│   ├── indexer.py      # 문서 인덱싱
│   └── drive_io.py     # Google Drive 연동
├── index/              # FAISS 인덱스 저장소
└── downloads/          # 다운로드된 문서
```

## 지원 기능

- **문서 처리**: PDF 텍스트 추출 및 청킹
- **벡터 검색**: FAISS 기반 유사도 검색
- **이미지 분석**: AWS 아키텍처 전문 분석
- **OCR**: 텍스트 추출 및 인식
- **웹 인터페이스**: Gradio 기반 사용자 친화적 UI

## 요구사항

- Python 3.8+
- OpenAI API 키
- Google Drive API 접근 권한
- Tesseract OCR (OCR 기능 사용 시)
