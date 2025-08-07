#!/bin/bash

# 환경 변수 로드
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 설정 (환경 변수에서 가져오거나 기본값 사용)
MC_ALIAS="local"
EXTERNAL_ENDPOINT="${MINIO_EXTERNAL_ENDPOINT:-http://100.97.183.123:19000}"
INTERNAL_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
ACCESS_KEY="${MINIO_ROOT_USER:-minio}"
SECRET_KEY="${MINIO_ROOT_PASSWORD:-miniosecret}"
NEW_USER="labelstudio"
NEW_PASS="labelpass"
BUCKET_NAME="${LABEL_STUDIO_S3_BUCKET:-aws-diagram-object-detection}"
PREFIX="${LABEL_STUDIO_S3_PREFIX:-preprocessed}"

echo "🔧 MinIO Label Studio 설정을 시작합니다..."
echo "📋 설정 정보:"
echo "  - 외부 Endpoint: $EXTERNAL_ENDPOINT"
echo "  - 내부 Endpoint: $INTERNAL_ENDPOINT"
echo "  - Access Key: $ACCESS_KEY"
echo "  - Bucket: $BUCKET_NAME"
echo "  - Prefix: $PREFIX"
echo ""

# 1. mc alias 등록 (외부 접근용)
echo "🔗 MinIO 클라이언트 alias를 설정합니다..."
mc alias set $MC_ALIAS $EXTERNAL_ENDPOINT $ACCESS_KEY $SECRET_KEY

# 2. 버킷 생성
echo "🪣 버킷을 생성합니다..."
mc mb ${MC_ALIAS}/${BUCKET_NAME} || echo "Bucket already exists."

# 3. 정책 파일 생성
echo "📄 정책 파일을 생성합니다..."
cat <<EOF > policy-labelstudio.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowListBucket",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::${BUCKET_NAME}"]
    },
    {
      "Sid": "AllowListPrefix",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::${BUCKET_NAME}"],
      "Condition": {
        "StringLike": {
          "s3:prefix": ["${PREFIX}", "${PREFIX}/*"]
        }
      }
    },
    {
      "Sid": "AllowFullAccessToPrefix",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": ["arn:aws:s3:::${BUCKET_NAME}/${PREFIX}/*"]
    },
    {
      "Sid": "AllowFullAccessToBucket",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": ["arn:aws:s3:::${BUCKET_NAME}/*"]
    }
  ]
}
EOF

# 4. 정책 등록
echo "🔐 정책을 등록합니다..."
mc admin policy create $MC_ALIAS labelstudio-policy policy-labelstudio.json

# 5. 사용자 등록
echo "👤 사용자를 등록합니다..."
mc admin user add $MC_ALIAS $NEW_USER $NEW_PASS

# 6. 정책 연결
echo "🔗 사용자에게 정책을 연결합니다..."
mc admin policy attach $MC_ALIAS --user $NEW_USER --policy labelstudio-policy

# 7. 테스트 파일 업로드
echo "📁 테스트 파일을 업로드합니다..."
mkdir -p /tmp/test-files
echo "test,data,value" > /tmp/test-files/test.csv
echo "This is a test text file" > /tmp/test-files/test.txt

mc cp /tmp/test-files/test.csv ${MC_ALIAS}/${BUCKET_NAME}/${PREFIX}/
mc cp /tmp/test-files/test.txt ${MC_ALIAS}/${BUCKET_NAME}/${PREFIX}/

# 8. 버킷 정책 설정
echo "🔒 버킷 정책을 설정합니다..."
mc policy set download ${MC_ALIAS}/${BUCKET_NAME}

echo ""
echo "✅ MinIO Label Studio 설정이 완료되었습니다!"
echo ""
echo "📋 Label Studio에서 사용할 정보:"
echo "  - Endpoint (Docker 내부): $INTERNAL_ENDPOINT"
echo "  - Endpoint (외부 접근): $EXTERNAL_ENDPOINT"
echo "  - Access Key: $NEW_USER"
echo "  - Secret Key: $NEW_PASS"
echo "  - Bucket: $BUCKET_NAME"
echo "  - Prefix: $PREFIX"
echo ""
echo "🔍 테스트 파일 확인:"
mc ls ${MC_ALIAS}/${BUCKET_NAME}/${PREFIX}/
echo ""
echo "💡 Label Studio 설정 시 Docker 내부 Endpoint를 사용하세요!"
