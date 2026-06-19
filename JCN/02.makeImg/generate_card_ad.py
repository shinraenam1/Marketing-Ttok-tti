import base64
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT").rstrip("/") + "/openai/v1"
api_key = os.getenv("AZURE_OPENAI_KEY")
deployment_name = "gpt-image-2"

# =============================================
# 광고 인풋 설정 (나중에 이 부분만 바꾸면 됨)
# =============================================
benefit      = "금리 5%"          # 핵심 혜택
product_name = "프리미엄 적금 카드" # 상품명
event_name   = "여름 특별 혜택"    # 이벤트명

# 플랫폼 선택: sns | blog | banner
platform = "sns"

# 플랫폼별 해상도
# gpt-image-2 조건: 16px 배수, 긴 변 ≤ 3840px, 비율 ≤ 3:1, 총 픽셀 655,360~8,294,400
platform_sizes = {
    "sns":    "1024x1024",   # 인스타그램 / 페이스북 정방형
    "blog":   "1216x640",    # 블로그 썸네일 (1.9:1)
    "banner": "1920x640",    # 홈페이지 배너 (3:1)
}

size = platform_sizes[platform]

# =============================================
# 프롬프트 구성
# =============================================
prompt = f"""
Create a professional and visually striking credit card advertisement image for the Korean market.

Product: {product_name}
Key Benefit: {benefit} annual interest rate
Event: {event_name}

Design requirements:
- Modern, premium banking advertisement style
- Feature a sleek, shiny premium credit card as the main centerpiece
- Display the benefit text "{benefit} 금리" prominently in large bold Korean typography
- Include the event title "{event_name}" in elegant Korean text
- Clean gradient background in deep blue and gold tones conveying trust and premium quality
- Subtle financial visual elements: upward trend graph, gold coins, sparkle effects
- High contrast, eye-catching layout optimized for {platform} platform
- No real people; focus on product visualization and graphic design
- Korean minimalist aesthetic with luxury feel
""".strip()

# =============================================
# 이미지 생성
# =============================================
client = OpenAI(
    base_url=endpoint,
    api_key=api_key,
)

print("=" * 50)
print(f"  플랫폼 : {platform}")
print(f"  해상도 : {size}")
print(f"  상품   : {product_name}")
print(f"  혜택   : {benefit}")
print(f"  이벤트 : {event_name}")
print("=" * 50)
print("이미지 생성 중...")

img = client.images.generate(
    model=deployment_name,
    prompt=prompt,
    n=1,
    size=size,
    quality="medium",
)

image_bytes = base64.b64decode(img.data[0].b64_json)
output_path = f"output_{platform}.png"
with open(output_path, "wb") as f:
    f.write(image_bytes)

print(f"✅ 이미지 저장 완료: {output_path}")
