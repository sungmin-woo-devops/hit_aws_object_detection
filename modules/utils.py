import cairosvg

def convert_svg_to_png(svg_content: str, output_size: tuple = (416, 416)) -> bytes:
    """
    SVG 내용을 PNG로 변환합니다.
    
    Args:
        svg_content: SVG 파일 내용 (문자열)
        output_size: 출력 이미지 크기 (width, height)
    
    Returns:
        PNG 이미지 바이트 데이터
    """
    try:
        # SVG를 PNG로 변환 (cairosvg 사용)
        png_data = cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            output_width=output_size[0],
            output_height=output_size[1],
            background_color='white'  # 배경색을 흰색으로 설정
        )
        return png_data
    except Exception as e:
        print(f"SVG 변환 실패: {e}")
        return None