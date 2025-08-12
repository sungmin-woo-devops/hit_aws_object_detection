# Google Drive API 설정 가이드

## 1. Google Cloud Console에서 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. 프로젝트 ID를 기억해두세요

## 2. Google Drive API 활성화

1. 왼쪽 메뉴에서 "API 및 서비스" > "라이브러리" 선택
2. "Google Drive API" 검색 후 클릭
3. "사용" 버튼 클릭

## 3. OAuth 2.0 클라이언트 ID 생성

1. "API 및 서비스" > "사용자 인증 정보" 선택
2. "사용자 인증 정보 만들기" > "OAuth 클라이언트 ID" 클릭
3. 애플리케이션 유형: "데스크톱 앱" 선택
4. 이름 입력 (예: "Drive API Client")
5. "만들기" 클릭

## 4. credentials.json 다운로드

1. 생성된 OAuth 2.0 클라이언트 ID 옆의 다운로드 버튼 클릭
2. 다운로드된 파일을 `mini_rag/credentials.json`으로 저장

## 5. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용 추가:

```env
# Google Drive 설정
DRIVE_FOLDER=your_google_drive_folder_id_here
SHARED_FOLDER=your_shared_drive_folder_id_here

# OpenAI 설정
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# 시스템 설정
DEBUG=false
LOG_LEVEL=INFO
```

### 폴더 ID 찾는 방법:
1. **Drive 폴더**: 개인 Google Drive 폴더
   - Google Drive에서 해당 폴더를 열기
   - URL에서 폴더 ID 확인: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
   - 또는 폴더를 우클릭 > "링크 복사" > URL에서 폴더 ID 추출

2. **Shared 폴더**: 공유 드라이브 폴더
   - 공유 드라이브에서 해당 폴더를 열기
   - URL에서 폴더 ID 확인: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
   - 공유 드라이브에 대한 접근 권한이 있어야 합니다

## 6. 실행

```bash
cd mini_rag
python drive_min.py
```

첫 실행 시 브라우저가 열리면서 Google 계정으로 로그인하여 권한을 부여해야 합니다.

## 문제 해결

### "폴더 ID가 설정되지 않았습니다" 오류:
1. `.env` 파일이 `mini_rag` 폴더에 있는지 확인
2. `DRIVE_FOLDER` 또는 `SHARED_FOLDER` 환경변수가 올바르게 설정되었는지 확인
3. 폴더 ID가 올바른 형식인지 확인 (예: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`)
4. 최소한 하나의 폴더 ID는 설정되어야 합니다

### "폴더에서 PDF 파일을 찾을 수 없습니다" 오류:
1. 폴더 ID가 올바른지 확인
2. 해당 폴더에 PDF 파일이 있는지 확인
3. 폴더에 대한 접근 권한이 있는지 확인

### 403 오류가 계속 발생하는 경우:
1. `credentials.json` 파일이 올바른 위치에 있는지 확인
2. Google Cloud Console에서 API가 활성화되었는지 확인
3. OAuth 동의 화면에서 테스트 사용자로 등록되었는지 확인

### 공유 드라이브 접근 오류:
- 공유 드라이브 ID가 올바른지 확인
- 해당 공유 드라이브에 대한 접근 권한이 있는지 확인

### Google Drive API 필드 오류:
- 최신 버전의 `google-api-python-client` 라이브러리 사용
- API 버전이 v3인지 확인
