#!/bin/bash

# Label Studio S3 Storage 설정 가이드

echo "📋 Label Studio S3 Storage 설정 가이드"
echo "======================================"
echo ""

# 환경 변수 로드
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🔧 Label Studio에서 S3 Storage를 설정하는 방법:"
echo ""
echo "1. Label Studio에 접속: http://localhost:8082"
echo ""
echo "2. Settings > Cloud Storage로 이동"
echo ""
echo "3. 'Add Source Storage' 클릭"
echo ""
echo "4. 다음 정보를 입력:"
echo "   - Storage Title: MinIO S3 Storage"
echo "   - Storage Type: Amazon S3"
echo "   - S3 Endpoint: ${LABEL_STUDIO_S3_ENDPOINT:-http://100.97.183.123:19000}"
echo "   - Access Key: ${LABEL_STUDIO_S3_ACCESS_KEY:-labelstudio}"
echo "   - Secret Key: ${LABEL_STUDIO_S3_SECRET_KEY:-labelpass}"
echo "   - Bucket Name: ${LABEL_STUDIO_S3_BUCKET:-aws-diagram-object-detection}"
echo "   - Prefix: ${LABEL_STUDIO_S3_PREFIX:-preprocessed}"
echo "   - Region Name: us-east-1"
echo ""
echo "5. 'Check Connection' 클릭하여 연결 확인"
echo ""
echo "6. 'Sync Storage' 클릭하여 동기화"
echo ""
echo "7. 파일 필터 설정 (선택사항):"
echo "   - .*csv or .*(jpeg|png|tiff) or .*w+-d+.text"
echo ""
echo "⚠️  중요: 외부 IP를 사용하므로 Endpoint는 http://100.97.183.123:19000을 사용하세요!"
echo ""
echo "🔍 문제 해결:"
echo "  - 연결 실패 시: ./status.sh로 서비스 상태 확인"
echo "  - 동기화 실패 시: docker logs infra_app_1로 로그 확인"
echo "  - 권한 문제 시: ./setup_minio_labelstudio.sh 재실행"
echo "  - CSP 오류 시: 브라우저 캐시 삭제 후 재시도"
echo ""
echo "📊 현재 설정된 정보:"
echo "  - MinIO Endpoint: ${LABEL_STUDIO_S3_ENDPOINT:-http://100.97.183.123:19000}"
echo "  - Bucket: ${LABEL_STUDIO_S3_BUCKET:-aws-diagram-object-detection}"
echo "  - Prefix: ${LABEL_STUDIO_S3_PREFIX:-preprocessed}"
echo "  - Access Key: ${LABEL_STUDIO_S3_ACCESS_KEY:-labelstudio}" 