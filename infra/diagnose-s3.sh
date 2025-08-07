#!/bin/bash

# S3 연결 및 동기화 문제 진단 스크립트

echo "🔍 S3 연결 및 동기화 문제 진단"
echo "================================"
echo ""

# 환경 변수 로드
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "📊 1. 서비스 상태 확인"
echo "----------------------"
docker-compose -f compose.full.yml ps
echo ""

echo "🌐 2. 네트워크 연결 확인"
echo "----------------------"
echo "Docker 네트워크 정보:"
docker network inspect infra_default 2>/dev/null | grep -A 10 "Containers" || echo "네트워크 정보를 찾을 수 없습니다"
echo ""

echo "🔗 3. MinIO 연결 테스트"
echo "----------------------"
MC_ALIAS="local"
EXTERNAL_ENDPOINT="${MINIO_EXTERNAL_ENDPOINT:-http://100.97.183.123:19000}"
INTERNAL_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"

echo "외부 Endpoint 테스트: $EXTERNAL_ENDPOINT"
mc alias set test-external $EXTERNAL_ENDPOINT ${MINIO_ROOT_USER:-minio} ${MINIO_ROOT_PASSWORD:-miniosecret} 2>/dev/null
if mc ls test-external/ 2>/dev/null; then
    echo "✅ 외부 연결 성공"
else
    echo "❌ 외부 연결 실패"
fi

echo "내부 Endpoint 테스트: $INTERNAL_ENDPOINT"
mc alias set test-internal $INTERNAL_ENDPOINT ${MINIO_ROOT_USER:-minio} ${MINIO_ROOT_PASSWORD:-miniosecret} 2>/dev/null
if mc ls test-internal/ 2>/dev/null; then
    echo "✅ 내부 연결 성공"
else
    echo "❌ 내부 연결 실패"
fi
echo ""

echo "📁 4. 버킷 및 파일 확인"
echo "----------------------"
BUCKET_NAME="${LABEL_STUDIO_S3_BUCKET:-aws-diagram-object-detection}"
PREFIX="${LABEL_STUDIO_S3_PREFIX:-preprocessed}"

echo "버킷 목록:"
mc ls local/ 2>/dev/null || echo "버킷 목록을 가져올 수 없습니다"
echo ""

echo "버킷 내용 ($BUCKET_NAME):"
mc ls local/$BUCKET_NAME/ 2>/dev/null || echo "버킷 내용을 가져올 수 없습니다"
echo ""

echo "Prefix 내용 ($PREFIX):"
mc ls local/$BUCKET_NAME/$PREFIX/ 2>/dev/null || echo "Prefix 내용을 가져올 수 없습니다"
echo ""

echo "🔐 5. 권한 확인"
echo "----------------------"
echo "사용자 목록:"
mc admin user list local 2>/dev/null || echo "사용자 목록을 가져올 수 없습니다"
echo ""

echo "정책 목록:"
mc admin policy list local 2>/dev/null || echo "정책 목록을 가져올 수 없습니다"
echo ""

echo "📋 6. Label Studio 로그 확인"
echo "----------------------"
echo "최근 Label Studio 로그 (마지막 20줄):"
docker logs infra_app_1 --tail=20 2>/dev/null || echo "Label Studio 로그를 가져올 수 없습니다"
echo ""

echo "🔧 7. 권장 해결 방법"
echo "----------------------"
echo "1. 서비스 재시작: ./restart.sh"
echo "2. MinIO 설정 재실행: ./setup_minio_labelstudio.sh"
echo "3. Label Studio 설정 가이드: ./labelstudio-s3-guide.sh"
echo "4. 정리 후 재시작: ./cleanup.sh && ./start.sh"
echo ""
echo "💡 Docker 내부 네트워크에서 http://minio:9000을 사용하세요!" 