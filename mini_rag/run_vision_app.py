#!/usr/bin/env python3
"""
Vision 기능만 포함된 Gradio 앱
"""

from dotenv import load_dotenv
import os
from pathlib import Path
import gradio as gr
import PIL.Image as Image

# 환경 변수 로드
load_dotenv()

# Vision 모듈 import
from core.vision import analyze_image, analyze_image_or_ocr, analyze_aws_architecture

def analyze_uploaded_image(image, use_ocr=False, extra_context="", analysis_type="aws_architecture", icon_json=""):
    """업로드된 이미지를 분석하는 함수"""
    if image is None:
        return "이미지를 업로드해주세요."
    
    try:
        # PIL Image로 변환
        if hasattr(image, 'convert'):
            pil_img = image
        else:
            pil_img = Image.fromarray(image)
        
        # 분석 타입에 따른 처리
        if analysis_type == "aws_architecture":
            result = analyze_aws_architecture(pil_img, detailed=True, include_recommendations=True)
        elif use_ocr:
            result = analyze_image_or_ocr(pil_img, ocr=True, extra_context=extra_context, icon_json=icon_json)
        else:
            result = analyze_image(pil_img, extra_context=extra_context, icon_json=icon_json)
        
        return result
    except Exception as e:
        return f"이미지 분석 중 오류가 발생했습니다: {str(e)}"

def on_image_upload(image):
    """이미지 업로드 시 텍스트박스 초기화"""
    if image is not None:
        return gr.update(value=""), gr.update(value="")  # extra_context, icon_json 초기화
    return gr.update(), gr.update()

# Gradio UI
with gr.Blocks(title="AWS 다이어그램 Vision 분석", theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🖼️ AWS 아키텍처 다이어그램 Vision 분석")
    gr.Markdown("AWS 다이어그램을 업로드하면 OpenAI Vision API를 통해 자동으로 분석합니다.")
    
    with gr.Row():
        with gr.Column(scale=1):
            image_input = gr.Image(
                label="AWS 다이어그램 업로드", 
                type="pil",
                height=400
            )
            
            with gr.Row():
                analysis_type = gr.Radio(
                    choices=["aws_architecture", "standard"], 
                    value="aws_architecture",
                    label="분석 타입",
                    info="AWS 아키텍처: 전문적 분석, Standard: 기본 분석"
                )
                ocr_checkbox = gr.Checkbox(
                    label="OCR 사용", 
                    value=False,
                    info="텍스트가 포함된 다이어그램에서 텍스트 추출"
                )
            
            analyze_btn = gr.Button("이미지 분석", variant="primary", size="lg")
            
            extra_context = gr.Textbox(
                label="추가 컨텍스트 (선택사항)", 
                placeholder="추가적인 정보나 특별한 요구사항이 있다면 입력하세요",
                lines=3
            )
            
            icon_json = gr.Textbox(
                label="아이콘 탐지 JSON (선택사항)", 
                placeholder="아이콘 탐지 결과 JSON을 입력하세요",
                lines=3
            )
            
        with gr.Column(scale=1):
            analysis_output = gr.Textbox(
                label="분석 결과", 
                lines=25, 
                max_lines=35,
                interactive=False
            )
    
    # 이벤트 연결
    analyze_btn.click(
        analyze_uploaded_image, 
        inputs=[image_input, ocr_checkbox, extra_context, analysis_type, icon_json], 
        outputs=[analysis_output]
    )
    
    # 이미지 업로드 시 텍스트박스 초기화
    image_input.change(
        on_image_upload,
        inputs=[image_input],
        outputs=[extra_context, icon_json]
    )

if __name__ == "__main__":
    print("AWS 다이어그램 Vision 분석 앱을 시작합니다...")
    print("브라우저에서 http://localhost:7860 으로 접속하세요.")
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860,
        share=False,
        show_error=True
    )
