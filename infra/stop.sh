#!/bin/bash

# MinIO + Label Studio 서비스 중지 스크립트

set -e

# 환경 변수 로드
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🛑 MinIO + Label Studio 서비스를 중지합니다..."

# Docker Compose로 서비스 중지 (orphan 컨테이너도 함께 제거)
echo "🐳 Docker Compose로 서비스를 중지합니다..."
docker-compose -f compose.full.yml down --remove-orphans

echo "✅ 서비스가 중지되었습니다!"
echo ""
echo "🔧 관리 명령어:"
echo "  - 서비스 시작: ./start.sh"
echo "  - 서비스 재시작: ./restart.sh" 