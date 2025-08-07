# 🔍 AWS Diagram Object Detection

AWS 아키텍처 다이어그램에서 서비스 아이콘을 자동으로 탐지하고 분류하는 AI 시스템입니다.

## 🎯 프로젝트 개요

AWS 클라우드 아키텍처 다이어그램에서 EC2, S3, Lambda 등의 서비스 아이콘을 자동으로 인식하여 다이어그램 분석을 자동화하는 프로젝트입니다. YOLOv8 기반 객체 탐지 모델을 사용하여 높은 정확도로 AWS 서비스 아이콘을 탐지합니다.

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   데이터 관리    │    │   모델 학습     │    │   웹 인터페이스  │
│   (MinIO)       │    │   (YOLOv8)      │    │   (Streamlit)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   라벨링 도구   │    │   모델 배포     │    │   실시간 탐지   │
│ (Label Studio)  │    │   (ONNX/TensorRT)│   │   (웹/API)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 프로젝트 구조

```
hit_aws_object_detection/
├── 📊 데이터 관리
│   ├── data/                    # 로컬 데이터 저장소
│   ├── AWS-Icon-Detector--4/    # 학습 데이터셋
│   └── DATA_MANAGEMENT.md       # 데이터 관리 가이드
│
├── 🤖 AI 모델
│   ├── train.py                 # 모델 학습 스크립트
│   ├── train.ipynb              # 학습 노트북
│   ├── data.yaml                # 데이터 설정
│   └── runs/                    # 학습 결과 저장
│
├── 🌐 웹 애플리케이션
│   └── streamlit-app/           # Streamlit 웹 인터페이스
│       ├── app.py               # 메인 애플리케이션
│       ├── models/              # 배포용 모델
│       └── samples/             # 테스트 이미지
│
├── 🐳 인프라 관리
│   └── infra/                   # Docker 기반 인프라
│       ├── compose.yml          # 서비스 구성
│       ├── start.sh             # 서비스 시작
│       └── stop.sh              # 서비스 중지
│
├── 🛠️ 유틸리티
│   ├── modules/                 # 공통 모듈
│   ├── utils/                   # 유틸리티 함수
│   └── training-pipeline/       # 학습 파이프라인
│
└── 📋 문서
    ├── README.md                # 프로젝트 가이드
    └── requirements.txt         # 의존성 목록
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd hit_aws_object_detection

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 인프라 서비스 시작

```bash
cd infra
./start.sh
```

**접속 정보:**
- MinIO API: http://localhost:19000
- MinIO Console: http://localhost:9001
- Label Studio: http://localhost:8080

### 3. 모델 학습

```bash
# 기본 학습 실행
python train.py

# 또는 Jupyter 노트북 사용
jupyter notebook train.ipynb
```

### 4. 웹 애플리케이션 실행

```bash
cd streamlit-app
streamlit run app.py
```

**접속:** http://localhost:8501

## 🔧 주요 기능

### 📊 데이터 관리
- **MinIO 기반 저장소**: 체계적인 데이터 라이프사이클 관리
- **자동 라벨링**: Label Studio를 통한 효율적인 주석 작업
- **버전 관리**: 데이터셋과 모델의 버전 추적

### 🤖 AI 모델
- **YOLOv8 기반**: 최신 객체 탐지 알고리즘 사용
- **다중 클래스**: AWS 서비스별 아이콘 분류
- **실시간 추론**: ONNX 최적화로 빠른 탐지

### 🌐 웹 인터페이스
- **Streamlit 기반**: 직관적인 웹 인터페이스
- **실시간 업로드**: 이미지 파일 즉시 분석
- **결과 시각화**: 탐지 결과를 시각적으로 표시

## 📈 성능 지표

- **정확도**: 85%+ mAP (mean Average Precision)
- **속도**: <100ms 추론 시간 (GPU 기준)
- **지원 클래스**: 50+ AWS 서비스 아이콘

## 🛠️ 개발 환경

### 시스템 요구사항
- **OS**: Linux (Ubuntu 20.04+)
- **Python**: 3.10+
- **GPU**: NVIDIA GPU (권장, CUDA 지원)
- **메모리**: 8GB+ RAM
- **저장소**: 50GB+ 여유 공간

### 주요 의존성
```python
ultralytics>=8.0.0      # YOLOv8 모델
torch>=2.0.0            # PyTorch
streamlit>=1.28.0       # 웹 인터페이스
opencv-python>=4.8.0    # 이미지 처리
minio>=7.1.0            # 객체 저장소
```

## 🔄 워크플로우

### 1. 데이터 수집 및 전처리
```python
# SVG 파일을 PNG로 변환
python utils/svg_to_png.py --input data/raw/svg/ --output data/processed/
```

### 2. 라벨링 작업
```bash
# Label Studio 접속
http://localhost:8080
```

### 3. 모델 학습
```python
# 학습 실행
python train.py --data data.yaml --epochs 100 --imgsz 320
```

### 4. 모델 배포
```python
# ONNX 변환
model.export(format='onnx', imgsz=320)
```

### 5. 웹 서비스 실행
```bash
cd streamlit-app
streamlit run app.py
```

## 📚 사용 예시

### 웹 인터페이스 사용법

1. **이미지 업로드**: AWS 아키텍처 다이어그램 이미지 선택
2. **자동 분석**: AI 모델이 서비스 아이콘 자동 탐지
3. **결과 확인**: 탐지된 아이콘과 신뢰도 점수 확인
4. **결과 다운로드**: 분석 결과 이미지 저장

### API 사용법

```python
from modules.detector import AWSIconDetector

# 모델 로드
detector = AWSIconDetector('models/best.pt')

# 이미지 분석
results = detector.detect('path/to/diagram.png')

# 결과 출력
for detection in results:
    print(f"서비스: {detection['class']}, 신뢰도: {detection['confidence']:.2f}")
```

## 🔧 고급 설정

### 환경 변수 설정

```bash
# .env 파일 생성
cp infra/env.example .env

# 환경 변수 편집
MINIO_ENDPOINT=http://localhost:19000
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=miniosecret
ROBOFLOW_API_KEY=your_api_key
```

### 커스텀 모델 학습

```python
# 커스텀 데이터셋으로 학습
model.train(
    data='custom_data.yaml',
    epochs=200,
    imgsz=416,
    batch=16,
    patience=20
)
```

## 🐛 문제 해결

### 일반적인 문제들

1. **GPU 메모리 부족**
   ```python
   # 배치 크기 줄이기
   model.train(batch=4)
   ```

2. **MinIO 연결 오류**
   ```bash
   # 서비스 상태 확인
   cd infra && ./status.sh
   ```

3. **모델 로딩 실패**
   ```python
   # ONNX 모델 재생성
   model.export(format='onnx')
   ```

## 🤝 기여하기

1. **Fork** 저장소
2. **Feature branch** 생성 (`git checkout -b feature/amazing-feature`)
3. **Commit** 변경사항 (`git commit -m 'Add amazing feature'`)
4. **Push** 브랜치 (`git push origin feature/amazing-feature`)
5. **Pull Request** 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

- **문서**: [DATA_MANAGEMENT.md](DATA_MANAGEMENT.md)
- **이슈**: GitHub Issues에 버그 리포트
- **문의**: 프로젝트 메인테이너에게 연락

---

**🔍 AWS Diagram Object Detection** - AWS 아키텍처 다이어그램의 자동화된 분석을 위한 AI 시스템