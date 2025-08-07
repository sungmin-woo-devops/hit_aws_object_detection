#!/bin/bash

# 기존 CLI 스크립트에서 Docker Compose로 마이그레이션
# 기존 데이터 보존: ~/DATA/smallpod/minio

set -e

echo "🚀 MinIO + Label Studio Docker Compose 마이그레이션 시작"

# 환경 변수 파일 확인
if [ ! -f .env ]; then
    echo "📝 .env 파일을 생성합니다..."
    cp env.example .env
    echo "✅ .env 파일이 생성되었습니다. 필요에 따라 설정을 수정하세요."
fi

# 환경 변수 로드
if [ -f .env ]; then
    echo "📋 환경 변수를 로드합니다..."
    export $(grep -v '^#' .env | xargs)
fi

# 기존 MinIO 컨테이너 중지 및 제거
echo "🛑 기존 MinIO 컨테이너를 중지합니다..."
docker stop minio-server 2>/dev/null || echo "기존 MinIO 컨테이너가 없습니다."
docker rm minio-server 2>/dev/null || echo "기존 MinIO 컨테이너가 제거되었습니다."

# 기존 네트워크 정리
echo "🧹 기존 네트워크를 정리합니다..."
docker network rm minio-network 2>/dev/null || echo "기존 네트워크가 없습니다."

# 데이터 디렉토리 확인
MINIO_DATA_PATH="${MINIO_DATA_PATH:-/home/smallpod/DATA/smallpod/minio}"
if [ ! -d "$MINIO_DATA_PATH" ]; then
    echo "📁 MinIO 데이터 디렉토리를 생성합니다: $MINIO_DATA_PATH"
    mkdir -p "$MINIO_DATA_PATH"
fi

# Docker Compose로 시작
echo "🐳 Docker Compose로 서비스를 시작합니다..."
docker-compose -f compose.minio.yml up -d

echo "⏳ 서비스가 시작되는 동안 잠시 기다립니다..."
sleep 10

# 서비스 상태 확인
echo "🔍 서비스 상태를 확인합니다..."
docker-compose -f compose.minio.yml ps

echo "✅ 마이그레이션이 완료되었습니다!"
echo ""
echo "📋 접속 정보:"
echo "  - MinIO API: http://localhost:19000"
echo "  - MinIO Console: http://localhost:9001"
echo "  - Label Studio: http://localhost:8080"
echo ""
echo "🔧 관리 명령어:"
echo "  - 서비스 시작: docker-compose -f compose.minio.yml up -d"
echo "  - 서비스 중지: docker-compose -f compose.minio.yml down"
echo "  - 로그 확인: docker-compose -f compose.minio.yml logs -f"
echo ""
echo "⚠️  기존 데이터 경로: $MINIO_DATA_PATH" 