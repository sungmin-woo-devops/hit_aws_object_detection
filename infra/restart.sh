#!/bin/bash

# MinIO + Label Studio 서비스 재시작 스크립트

set -e

# 환경 변수 로드
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🔄 MinIO + Label Studio 서비스를 재시작합니다..."

# 서비스 중지 (orphan 컨테이너도 함께 제거)
echo "🛑 서비스를 중지합니다..."
docker-compose -f compose.full.yml down --remove-orphans

# 잠시 대기
echo "⏳ 잠시 대기합니다..."
sleep 5

# 서비스 시작
echo "🚀 서비스를 시작합니다..."
docker-compose -f compose.full.yml up -d

echo "⏳ 서비스가 시작되는 동안 잠시 기다립니다..."
sleep 15

# 서비스 상태 확인
echo "🔍 서비스 상태를 확인합니다..."
docker-compose -f compose.full.yml ps

echo "✅ 서비스가 재시작되었습니다!"
echo ""
echo "📋 접속 정보:"
echo "  - MinIO API: http://localhost:19000"
echo "  - MinIO Console: http://localhost:9001"
echo "  - Label Studio: http://localhost:8082"
echo "  - Label Studio (Alt): http://localhost:8083" 