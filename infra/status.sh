#!/bin/bash

# MinIO + Label Studio 서비스 상태 확인 스크립트

# 환경 변수 로드
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🔍 MinIO + Label Studio 서비스 상태를 확인합니다..."
echo ""

# Docker Compose 서비스 상태
echo "📊 Docker Compose 서비스 상태:"
docker-compose -f compose.full.yml ps
echo ""

# 컨테이너 로그 확인
echo "📋 최근 로그 (마지막 10줄):"
echo "MinIO 로그:"
docker-compose -f compose.full.yml logs --tail=10 minio
echo ""

echo "Label Studio App 로그:"
docker-compose -f compose.full.yml logs --tail=10 app
echo ""

echo "Label Studio Nginx 로그:"
docker-compose -f compose.full.yml logs --tail=10 nginx
echo ""

echo "PostgreSQL 로그:"
docker-compose -f compose.full.yml logs --tail=10 db
echo ""

# 포트 사용 현황
echo "🌐 포트 사용 현황:"
echo "MinIO API (19000):"
netstat -tlnp | grep :19000 || echo "포트 19000이 사용되지 않음"
echo ""

echo "MinIO Console (9001):"
netstat -tlnp | grep :9001 || echo "포트 9001이 사용되지 않음"
echo ""

echo "Label Studio Nginx (8082):"
netstat -tlnp | grep :8082 || echo "포트 8082이 사용되지 않음"
echo ""

echo "Label Studio Nginx Alt (8083):"
netstat -tlnp | grep :8083 || echo "포트 8083이 사용되지 않음"
echo ""

# 데이터 디렉토리 확인
MINIO_DATA_PATH="${MINIO_DATA_PATH:-/home/smallpod/DATA/smallpod/minio}"
echo "📁 MinIO 데이터 디렉토리: $MINIO_DATA_PATH"
if [ -d "$MINIO_DATA_PATH" ]; then
    echo "✅ 데이터 디렉토리가 존재합니다"
    echo "📊 디렉토리 크기: $(du -sh "$MINIO_DATA_PATH" | cut -f1)"
else
    echo "❌ 데이터 디렉토리가 존재하지 않습니다"
fi

POSTGRES_DATA_DIR="${POSTGRES_DATA_DIR:-./postgres-data}"
echo "📁 PostgreSQL 데이터 디렉토리: $POSTGRES_DATA_DIR"
if [ -d "$POSTGRES_DATA_DIR" ]; then
    echo "✅ 데이터 디렉토리가 존재합니다"
    echo "📊 디렉토리 크기: $(du -sh "$POSTGRES_DATA_DIR" | cut -f1)"
else
    echo "❌ 데이터 디렉토리가 존재하지 않습니다"
fi 