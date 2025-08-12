# AWS 다이어그램 Vision 분석 기능

## 개요
이 모듈은 AWS 아키텍처 다이어그램을 OpenAI Vision API를 통해 분석하는 기능을 제공합니다.

## 주요 기능

### 1. 이미지 분석 타입
- **AWS 아키텍처**: AWS 서비스 전문 분석 (기본값)
- **Standard**: 일반적인 이미지 분석

### 2. OCR 기능
- 텍스트가 포함된 다이어그램에서 텍스트 추출
- 선택적 기능 (체크박스로 활성화/비활성화)

### 3. 추가 컨텍스트
- 분석에 추가 정보 제공
- 선택적 입력 필드

### 4. 아이콘 탐지 JSON
- 외부 아이콘 탐지 결과 입력
- 선택적 입력 필드

## 사용법

### Vision 전용 앱 실행 (권장)
```bash
python run_vision_app.py
```

### 전체 RAG + Vision 앱 실행
```bash
python gradio_app.py
```

1. **이미지 업로드**: AWS 다이어그램 이미지 업로드
2. **분석 타입 선택**: AWS 아키텍처 또는 Standard
3. **OCR 사용 여부**: 텍스트 추출이 필요한 경우 체크
4. **추가 컨텍스트**: 필요한 경우 추가 정보 입력
5. **아이콘 탐지 JSON**: 외부 탐지 결과가 있는 경우 입력
6. **분석 실행**: "이미지 분석" 버튼 클릭

### 프로그래밍 방식 사용
```python
from core.vision import analyze_image, analyze_image_or_ocr, analyze_aws_architecture
import PIL.Image as Image

# 이미지 로드
image = Image.open("aws_diagram.png")

# 1. 기본 분석
result = analyze_image(image, extra_context="추가 정보")

# 2. OCR 포함 분석
result = analyze_image_or_ocr(image, ocr=True, extra_context="OCR 테스트")

# 3. AWS 아키텍처 전용 분석
result = analyze_aws_architecture(image)
```

## 설치 요구사항

### 필수 패키지
```bash
pip install -r requirements.txt
```

### OCR 기능 사용 시
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# https://github.com/UB-Mannheim/tesseract/wiki 에서 설치
```

## 환경 변수 설정

`.env` 파일에 다음을 설정:
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini  # 또는 gpt-4o
```

## 분석 결과 예시

### 구조화 JSON의 역할
분석 결과에서 **구조화 JSON**은 다음과 같은 역할을 합니다:

1. **정확한 서비스 식별**: AWS 서비스와 리소스를 정확히 분류
2. **구성 요소 정리**: 다이어그램의 모든 구성 요소를 체계적으로 정리
3. **데이터 흐름 파악**: 서비스 간 연결 관계를 명확히 표시
4. **네트워킹 정보**: VPC, 서브넷, 보안 그룹 등 네트워크 구성 정리
5. **저장소 정보**: 데이터베이스, 스토리지 등 데이터 저장소 정보

### AWS 아키텍처 분석 예시
```
{
  "services": [
    {"name": "Amazon EC2", "count": 2, "labels": ["Web Server", "Application Server"]},
    {"name": "Amazon RDS", "count": 1, "labels": ["Database"]}
  ],
  "connections": [
    {"from": "EC2", "to": "RDS", "protocol": "MySQL", "notes": "데이터베이스 연결"}
  ],
  "networking": {
    "vpcs": ["VPC-12345"],
    "subnets": ["Public Subnet", "Private Subnet"],
    "security_groups": ["Web SG", "DB SG"]
  },
  "data_stores": [
    {"name": "RDS MySQL", "notes": "관계형 데이터베이스"}
  ]
}

## 상세 분석

### 구성 요소
- **EC2 인스턴스**: 웹 서버와 애플리케이션 서버 역할
- **RDS**: MySQL 데이터베이스 서비스

### 데이터 흐름
1. 사용자 요청 → EC2 웹 서버
2. EC2 웹 서버 → EC2 애플리케이션 서버
3. EC2 애플리케이션 서버 → RDS 데이터베이스

### 보안 고려사항
- VPC 내부에서 프라이빗 서브넷 사용
- 보안 그룹으로 접근 제어
```

## 문제 해결

### OCR 기능이 작동하지 않는 경우
1. Tesseract가 설치되어 있는지 확인
2. `pytesseract` 패키지가 설치되어 있는지 확인
3. 시스템 PATH에 Tesseract가 포함되어 있는지 확인

### 이미지 분석이 실패하는 경우
1. OpenAI API 키가 올바르게 설정되어 있는지 확인
2. 이미지 형식이 지원되는지 확인 (JPEG, PNG, GIF 등)
3. 이미지 크기가 너무 크지 않은지 확인 (자동으로 리사이즈됨)

### 텍스트박스가 초기화되지 않는 경우
- 이미지를 다시 업로드하면 자동으로 초기화됩니다
- 수동으로 텍스트를 지우고 입력할 수 있습니다

### Gradio 앱 상호작용 문제
- `run_vision_app.py`를 사용하여 Vision 전용 앱을 실행하세요
- 브라우저에서 http://localhost:7860 으로 접속하세요

## 성능 최적화

### 이미지 크기
- 최대 너비 1600px로 자동 리사이즈
- JPEG 품질 90%로 최적화

### 분석 속도
- `gpt-4o-mini` 모델 사용 권장 (빠른 응답)
- `gpt-4o` 모델은 더 정확하지만 느림

## 라이선스
이 프로젝트는 MIT 라이선스 하에 배포됩니다.
