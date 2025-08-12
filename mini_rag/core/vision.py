import base64, io, json, PIL.Image as Image
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.prompts import VISION_SYS

def _img_to_b64(pil: Image.Image, max_w=1600, quality=90):
    """이미지를 base64로 인코딩하고 크기 최적화"""
    w,h = pil.size
    if w>max_w:
        pil = pil.resize((max_w, int(h*max_w/w)), Image.LANCZOS)
    buf = io.BytesIO(); pil.save(buf, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def analyze_image(pil_img, *, extra_context="", icon_json="", json_only=False, model="gpt-4o-mini"):
    """AWS 다이어그램 이미지 분석"""
    b64 = _img_to_b64(pil_img)
    llm = ChatOpenAI(model=model, temperature=0.1)
    
    # 개선된 프롬프트 구성
    context_parts = []
    if extra_context:
        context_parts.append(f"추가 컨텍스트:\n{extra_context}")
    if icon_json:
        context_parts.append(f"아이콘 탐지 결과(JSON):\n{icon_json}")
    
    context_text = "\n\n".join(context_parts) if context_parts else ""
    
    human = [
        {"type":"text","text":f"{context_text}\n\n이 AWS 아키텍처 다이어그램을 분석해주세요."},
        {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}},
        {"type":"text","text":"다음 순서로 분석해주세요:\n1. 구조화된 JSON 형태로 AWS 서비스와 구성요소 정리\n2. 한국어로 상세한 아키텍처 해설\n\nJSON은 다음과 같은 형식으로 작성하세요:\n{\n  \"services\": [{\"name\": \"서비스명\", \"count\": 개수, \"labels\": [\"라벨1\", \"라벨2\"]}],\n  \"connections\": [{\"from\": \"시작점\", \"to\": \"도착점\", \"protocol\": \"프로토콜\", \"notes\": \"설명\"}],\n  \"networking\": {\"vpcs\": [], \"subnets\": [], \"security_groups\": []},\n  \"data_stores\": [{\"name\": \"저장소명\", \"notes\": \"설명\"}]\n}"}
    ]
    
    res = llm.invoke([SystemMessage(content=VISION_SYS), HumanMessage(content=human)])
    return res.content

def analyze_image_or_ocr(pil_img, *, ocr=True, icon_json="", extra_context="", model="gpt-4o-mini"):
    """OCR 기능을 포함한 이미지 분석"""
    ctx = extra_context or ""
    if ocr:
        t = _ocr_text(pil_img)
        if t and not t.startswith("OCR 기능을 사용하려면") and not t.startswith("OCR 오류"):
            ctx += f"\n\n[OCR 텍스트]\n{t}"
    return analyze_image(pil_img, extra_context=ctx, icon_json=icon_json, model=model)

def _ocr_text(pil_img):
    """OCR을 통한 텍스트 추출 (선택적 기능)"""
    try:
        import pytesseract
        return pytesseract.image_to_string(pil_img, lang="eng")
    except ImportError:
        return "OCR 기능을 사용하려면 pytesseract를 설치하세요: pip install pytesseract"
    except Exception as e:
        return f"OCR 오류: {str(e)}"

def analyze_aws_architecture(pil_img, *, detailed=True, include_recommendations=True, model="gpt-4o-mini"):
    """AWS 아키텍처 전용 분석 함수"""
    b64 = _img_to_b64(pil_img)
    llm = ChatOpenAI(model=model, temperature=0.1)
    
    # AWS 아키텍처 전용 시스템 프롬프트
    aws_sys_prompt = """당신은 AWS 아키텍처 전문가입니다. 다이어그램을 분석하여 다음을 제공하세요:

1. **구성 요소 식별**: 각 AWS 서비스와 리소스
2. **아키텍처 패턴**: 사용된 패턴 (예: 3-tier, microservices, serverless)
3. **데이터 흐름**: 서비스 간 데이터 이동 경로
4. **보안 분석**: 보안 그룹, IAM, 암호화 등
5. **성능 고려사항**: 확장성, 가용성, 지연시간
6. **비용 최적화**: 개선 가능한 영역
7. **모범 사례**: AWS Well-Architected Framework 기준

구체적이고 실용적인 분석을 제공하세요."""

    human = [
        {"type":"text","text":"이 AWS 아키텍처 다이어그램을 전문적으로 분석해주세요."},
        {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}},
        {"type":"text","text":"구성 요소, 데이터 흐름, 보안, 성능, 비용 최적화 관점에서 분석해주세요."}
    ]
    
    res = llm.invoke([SystemMessage(content=aws_sys_prompt), HumanMessage(content=human)])
    return res.content
