# MinIO + Label Studio 인프라 설정

이 디렉토리는 MinIO와 Label Studio를 Docker Compose로 관리하기 위한 설정 파일들을 포함합니다.

## 📁 파일 구조

```
infra/
├── compose.full.yml          # MinIO + Label Studio 통합 설정 (권장)
├── compose.minio.yml         # MinIO 전용 설정
├── compose.yml               # Label Studio 전용 설정
├── setup_minio_labelstudio.sh # MinIO 사용자/정책 설정 스크립트
├── policy-labelstudio.json   # Label Studio용 S3 정책
├── env.example              # 환경 변수 예제
├── migrate_to_compose.sh    # CLI에서 Compose로 마이그레이션
├── start.sh                 # 서비스 시작
├── stop.sh                  # 서비스 중지
├── restart.sh               # 서비스 재시작
├── status.sh                # 서비스 상태 확인
├── cleanup.sh               # Orphan 컨테이너 정리
├── start-minio-only.sh      # MinIO만 시작
├── diagnose-s3.sh           # S3 연결 문제 진단
├── labelstudio-s3-guide.sh  # Label Studio S3 설정 가이드
└── README.md               # 이 파일
```

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 환경 변수 파일 생성
cp env.example .env

# 필요에 따라 .env 파일 수정
# MINIO_ROOT_USER=minio
# MINIO_ROOT_PASSWORD=miniosecret
# MINIO_DATA_PATH=/home/smallpod/DATA/smallpod/minio
```

### 2. 서비스 시작
```bash
# 실행 권한 부여
chmod +x *.sh

# 통합 서비스 시작 (권장)
./start.sh

# 또는 개별 서비스 시작
./start-minio-only.sh  # MinIO만 시작
```

### 3. 접속 확인
- **MinIO API**: http://localhost:19000
- **MinIO Console**: http://localhost:9001
- **Label Studio**: http://localhost:8082
- **Label Studio API**: http://localhost:8083

## 🔧 관리 명령어

| 명령어 | 설명 |
|--------|------|
| `./start.sh` | 통합 서비스 시작 |
| `./stop.sh` | 서비스 중지 |
| `./restart.sh` | 서비스 재시작 |
| `./status.sh` | 서비스 상태 확인 |
| `./cleanup.sh` | Orphan 컨테이너 정리 |
| `./start-minio-only.sh` | MinIO만 시작 |

## 🔍 문제 해결

### S3 Storage 동기화 문제

Label Studio에서 MinIO S3 Storage 동기화가 실패하는 경우:

1. **진단 실행**:
```bash
./diagnose-s3.sh
```

2. **MinIO 설정 재실행**:
```bash
./setup_minio_labelstudio.sh
```

3. **Label Studio 설정 가이드 확인**:
```bash
./labelstudio-s3-guide.sh
```

4. **전체 문제 해결 스크립트 실행**:
```bash
./fix-s3-sync.sh
```

### 주요 해결 방법

1. **외부 IP 사용**: Label Studio에서 S3 Endpoint를 `http://100.97.183.123:19000`으로 설정
2. **브라우저 캐시 삭제**: CSP 오류 해결을 위해 브라우저 캐시 삭제
3. **권한 확인**: `labelstudio` 사용자가 올바른 정책을 가지고 있는지 확인
4. **서비스 재시작**: 설정 변경 후 서비스 재시작

### Label Studio S3 설정

Label Studio에서 S3 Storage를 설정할 때:

- **S3 Endpoint**: `http://100.97.183.123:19000` (외부 IP)
- **Access Key**: `labelstudio`
- **Secret Key**: `labelpass`
- **Bucket Name**: `aws-diagram-object-detection`
- **Prefix**: `preprocessed`
- **Region Name**: `us-east-1`

### 일반적인 오류 해결

#### S3StorageError: Debugging info is not available
- **원인**: Label Studio가 도메인을 인식하지 못함
- **해결**: 외부 IP 주소 사용 (`http://100.97.183.123:19000`)

#### Content-Security-Policy 오류
- **원인**: 브라우저 CSP 정책 위반
- **해결**: 브라우저 캐시 삭제 또는 시크릿 모드 사용

#### Sync Failed
- **원인**: 권한 부족 또는 연결 실패
- **해결**: MinIO 사용자/정책 재설정

## 📊 서비스 구성

### MinIO Object Storage
- **이미지**: minio/minio:RELEASE.2025-04-22T22-12-26Z
- **API 포트**: 19000 (외부), 9000 (내부)
- **Console 포트**: 9001
- **데이터 경로**: `~/DATA/smallpod/minio`
- **기본 계정**: minio / miniosecret
- **Label Studio 계정**: labelstudio / labelpass

### Label Studio
- **이미지**: heartexlabs/label-studio:latest
- **메인 포트**: 8082 (Nginx)
- **API 포트**: 8083
- **데이터베이스**: PostgreSQL
- **데이터 경로**: `./mydata`

### PostgreSQL Database
- **이미지**: pgautoupgrade/pgautoupgrade:13-alpine
- **포트**: 5432 (내부)
- **데이터 경로**: `./postgres-data`

### Prometheus (모니터링)
- **이미지**: quay.io/prometheus/prometheus:v2.37.1
- **포트**: 9090 (내부)
- **설정**: `./prometheus/minio/prometheus.yml`

## 🔄 전체 사용 흐름

### 1. 인프라 시작
```bash
# 1. 환경 설정
cp env.example .env

# 2. 서비스 시작
./start.sh

# 3. 상태 확인
./status.sh
```

### 2. MinIO 설정
```bash
# 1. MinIO 사용자 및 정책 설정
./setup_minio_labelstudio.sh

# 2. 설정 확인
./diagnose-s3.sh
```

### 3. Label Studio 설정
```bash
# 1. 설정 가이드 확인
./labelstudio-s3-guide.sh

# 2. Label Studio에서 S3 Storage 설정
# - Endpoint: http://minio:9000
# - Access Key: labelstudio
# - Secret Key: labelpass
# - Bucket: aws-diagram-object-detection
# - Prefix: preprocessed
```

## 🚨 문제 해결 체크리스트

- [ ] 서비스가 정상적으로 실행 중인가? (`./status.sh`)
- [ ] MinIO에 접근할 수 있는가? (http://localhost:19000)
- [ ] Label Studio에 접근할 수 있는가? (http://localhost:8082)
- [ ] MinIO 사용자 및 정책이 설정되었는가? (`./setup_minio_labelstudio.sh`)
- [ ] Label Studio에서 올바른 Endpoint를 사용하고 있는가? (`http://minio:9000`)
- [ ] 버킷에 파일이 있는가? (`mc ls local/aws-diagram-object-detection/preprocessed/`)

## 📝 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `MINIO_ROOT_USER` | MinIO 루트 사용자 | minio |
| `MINIO_ROOT_PASSWORD` | MinIO 루트 비밀번호 | miniosecret |
| `MINIO_DATA_PATH` | MinIO 데이터 경로 | ~/DATA/smallpod/minio |
| `MINIO_ENDPOINT` | Docker 내부 Endpoint | http://minio:9000 |
| `MINIO_EXTERNAL_ENDPOINT` | 외부 접근 Endpoint | http://100.97.183.123:19000 |
| `LABEL_STUDIO_HOST` | Label Studio 호스트 | http://localhost:8082 |
| `POSTGRES_DATA_DIR` | PostgreSQL 데이터 경로 | ./postgres-data | 