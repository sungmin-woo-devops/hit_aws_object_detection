#!/bin/bash

# S3 동기화 문제 해결 스크립트

echo "🔧 S3 동기화 문제 해결 스크립트"
echo "================================"
echo ""

# 환경 변수 로드
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "📋 문제 해결 단계:"
echo ""

echo "1. 🔍 현재 상태 확인"
echo "----------------------"
./status.sh
echo ""

echo "2. 🧹 브라우저 캐시 삭제 안내"
echo "----------------------"
echo "브라우저에서 다음을 수행하세요:"
echo "  - Ctrl+Shift+Delete (캐시 삭제)"
echo "  - 또는 시크릿 모드에서 접속"
echo ""

echo "3. 🔧 MinIO 설정 재실행"
echo "----------------------"
./setup_minio_labelstudio.sh
echo ""

echo "4. 🔄 서비스 재시작"
echo "----------------------"
./restart.sh
echo ""

echo "5. 📊 연결 테스트"
echo "----------------------"
echo "MinIO 연결 테스트:"
curl -s -o /dev/null -w "%{http_code}" http://100.97.183.123:19000 || echo "연결 실패"
echo ""

echo "6. 📋 Label Studio 설정 가이드"
echo "----------------------"
./labelstudio-s3-guide.sh
echo ""

echo "7. 🔍 문제 진단"
echo "----------------------"
./diagnose-s3.sh
echo ""

echo "✅ 해결 단계 완료!"
echo ""
echo "💡 다음 단계:"
echo "1. 브라우저 캐시를 삭제하세요"
echo "2. Label Studio에 다시 접속하세요: http://localhost:8082"
echo "3. S3 Storage 설정에서 외부 IP를 사용하세요: http://100.97.183.123:19000"
echo "4. 'Check Connection' 후 'Sync Storage'를 시도하세요"
echo ""
echo "🚨 여전히 문제가 있다면:"
echo "  - docker logs infra_app_1 --tail=50"
echo "  - ./diagnose-s3.sh" 