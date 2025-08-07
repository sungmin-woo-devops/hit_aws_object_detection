#!/bin/bash

# MinIO + Label Studio 서비스 시작 스크립트

set -e

echo "🚀 MinIO + Label Studio 서비스를 시작합니다..."

# 환경 변수 파일 확인
if [ ! -f .env ]; then
    echo "📝 .env 파일을 생성합니다..."
    cp env.example .env
    echo "✅ .env 파일이 생성되었습니다."
fi

# 환경 변수 로드
if [ ! -f .env ]; then
    echo "📋 환경 변수를 로드합니다..."
    export $(grep -v '^#' .env | xargs)
fi

# 데이터 디렉토리 확인
MINIO_DATA_PATH="${MINIO_DATA_PATH:-/home/smallpod/DATA/smallpod/minio}"
if [ ! -d "$MINIO_DATA_PATH" ]; then
    echo "📁 MinIO 데이터 디렉토리를 생성합니다: $MINIO_DATA_PATH"
    mkdir -p "$MINIO_DATA_PATH"
fi

# PostgreSQL 데이터 디렉토리 확인
POSTGRES_DATA_DIR="${POSTGRES_DATA_DIR:-./postgres-data}"
if [ ! -d "$POSTGRES_DATA_DIR" ]; then
    echo "📁 PostgreSQL 데이터 디렉토리를 생성합니다: $POSTGRES_DATA_DIR"
    mkdir -p "$POSTGRES_DATA_DIR"
fi

# Docker Compose로 서비스 시작
echo "🐳 Docker Compose로 서비스를 시작합니다..."
docker-compose -f compose.full.yml up -d

echo "⏳ 서비스가 시작되는 동안 잠시 기다립니다..."
sleep 15

# MinIO 정책 적용
echo "🔐 MinIO 정책을 적용합니다..."
mc --version
mc alias set myminio http://localhost:19000 minio miniosecret
mc admin policy create myminio labelstudio-policy ./labelstudio-policy.json
mc admin policy set myminio labelstudio-policy user=minio
echo "✅ 정책이 적용되었습니다."

# 서비스 상태 확인
echo "🔍 서비스 상태를 확인합니다..."
docker-compose -f compose.full.yml ps

echo "✅ 서비스가 시작되었습니다!"
echo ""
echo "📋 접속 정보:"
echo "  - MinIO API: http://localhost:19000"
echo "  - MinIO Console: http://localhost:9001"
echo "  - Label Studio: http://localhost:8082"
echo "  - Label Studio (Alt): http://localhost:8083"
echo ""
echo "🔧 관리 명령어:"
echo "  - 서비스 중지: ./stop.sh"
echo "  - 로그 확인: docker-compose -f compose.full.yml logs -f"