#!/bin/bash

# AWS 다이어그램 Vision 분석 앱 실행 스크립트

echo "🚀 AWS 다이어그램 Vision 분석 앱을 시작합니다..."

# Python 가상환경 확인
if [ -d "venv" ]; then
    echo "📦 가상환경을 활성화합니다..."
    source venv/bin/activate
fi

# 의존성 확인
echo "🔍 의존성을 확인합니다..."
python -c "import gradio, PIL, langchain_openai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 필요한 패키지가 설치되지 않았습니다."
    echo "다음 명령어로 설치하세요:"
    echo "pip install -r requirements.txt"
    exit 1
fi

# 환경 변수 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. 환경 변수를 설정하세요."
    echo "OPENAI_API_KEY=your_api_key"
    echo "OPENAI_MODEL=gpt-4o-mini"
fi

# 앱 실행
echo "🌐 Vision 앱을 시작합니다..."
echo "브라우저에서 http://localhost:7860 으로 접속하세요."
echo "종료하려면 Ctrl+C를 누르세요."
echo ""

python run_vision_app.py
