#!/bin/bash

# Orphan 컨테이너 정리 스크립트

set -e

echo "🧹 Orphan 컨테이너를 정리합니다..."

# 모든 서비스 중지 및 orphan 컨테이너 제거
echo "🛑 모든 서비스를 중지합니다..."
docker compose -f compose.full.yml down --remove-orphans
docker compose -f compose.minio.yml down --remove-orphans
docker compose -f compose.yml down --remove-orphans

# 사용하지 않는 컨테이너, 네트워크, 볼륨 정리
echo "🗑️ 사용하지 않는 Docker 리소스를 정리합니다..."
docker system prune -f

echo "✅ 정리가 완료되었습니다!"
echo ""
echo "🔧 다음 명령어로 서비스를 시작할 수 있습니다:"
echo "  - 전체 서비스: ./start.sh"
echo "  - MinIO만: ./start-minio-only.sh" 