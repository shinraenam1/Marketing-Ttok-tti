import os

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT").rstrip("/") + "/openai/v1"
api_key    = os.getenv("AZURE_OPENAI_KEY")
DEPLOYMENT = "gpt-image-2"

client = OpenAI(base_url=endpoint, api_key=api_key)

PROMPT_ONLY_DEFAULT_SIZE = "816x816"
DEFAULT_MARKETING_FIXED_PROMPT = """부산은행 금융 광고 이미지 생성. 브랜드 아이덴티티에 맞는 신뢰감 있는 디자인으로 제작.
입력된 상품종류, 혜택, 컨셉 정보를 기반으로 금융 서비스 홍보용 이미지 구성.
깔끔하고 현대적인 레이아웃, 고급스러운 금융회사 광고 스타일, 과도한 장식 없이 핵심 메시지가 잘 보이도록 제작.
이미지와 문구 배치는 균형 있게 배치하고 가독성 높은 타이포그래피 적용.
선정적/폭력적/과장 광고 요소 없이 친근하고 전문적인 부산은행 브랜드 이미지 유지."""

MARKETING_FIXED_PROMPT = (
    os.getenv("BNK_MARKETING_FIXED_PROMPT", "").replace("\\n", "\n").strip()
    or DEFAULT_MARKETING_FIXED_PROMPT
)

# 플랫폼별 최소 해상도 (gpt-image-2: 16px 배수, 655,360 ~ 8,294,400 px)
PLATFORM_SIZES = {
    "sns":    "816x816",    # 665,856 px
    "blog":   "1024x640",  # 655,360 px (최소)
    "banner": "1440x480",  # 691,200 px, 3:1
}


# ──────────────────────────────────────────
#  프롬프트 구성
# ──────────────────────────────────────────
def build_prompt(product: str, benefit: str, concept: str, platform: str) -> str:
    return f"""
Create a high-quality professional Korean banking advertisement image for BNK Busan Bank.

[Product Information]
- Product Type : {product}
- Key Benefit  : {benefit}
- Ad Concept   : {concept}
- Platform     : {platform}

[Brand Identity — BNK 부산은행]
- Primary color  : Deep crimson red (#C8102E) — use as bold accent
- Secondary color: Dark charcoal gray (#54534A)
- Background     : Clean white or very light warm gray
- Style          : Premium Korean financial institution, trustworthy, modern

[Design Requirements]
- Prominent display of the benefit "{benefit}" in large, bold Korean typography
- Clean, modern layout with generous white space — no clutter
- Subtle financial motifs: geometric shapes, soft gradients, upward growth lines
- Crimson red accent bars, lines, or shapes to reinforce brand identity
- Ad concept "{concept}" should influence the overall visual mood and imagery
- Balanced composition suitable for {platform} format
- NO logos, NO brand names, NO people
- Convey trust, stability, prosperity, and financial expertise
- High visual impact with professional Korean advertising aesthetics
""".strip()


def build_prompt_only_marketing_prompt(user_prompt: str) -> str:
    return f"""
부산은행 금융 광고 이미지를 제작한다.

[반드시 유지할 원칙]
{MARKETING_FIXED_PROMPT}

[출력 품질 가이드]
- Korean copy must be natural, concise, and legible.
- Use trustworthy, premium financial-ad visual tone.
- Keep hierarchy clear: headline > core benefit > support text.
- Avoid clutter and avoid tiny unreadable text.

[사용자 마케팅 요구 프롬프트]
{user_prompt}
""".strip()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/prompt-demo")
def prompt_demo():
    return render_template("prompt_demo.html")


@app.route("/generate", methods=["POST"])
def generate():
    data     = request.get_json()
    product  = data.get("product", "").strip()
    benefit  = data.get("benefit", "").strip()
    concept  = data.get("concept", "").strip()
    platform = data.get("platform", "sns")

    if not product or not benefit:
        return jsonify({"error": "상품종류와 혜택은 필수 입력입니다."}), 400

    size   = PLATFORM_SIZES.get(platform, "816x816")
    prompt = build_prompt(product, benefit, concept, platform)

    try:
        resp = client.images.generate(
            model=DEPLOYMENT,
            prompt=prompt,
            n=1,
            size=size,
            quality="low",
        )
        return jsonify({
            "image": resp.data[0].b64_json,
            "size": size,
            "prompt": prompt,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generate-from-prompt", methods=["POST"])
def generate_from_prompt():
    data = request.get_json() or {}
    user_prompt = data.get("prompt", "").strip()

    if not user_prompt:
        return jsonify({"error": "프롬프트를 입력해주세요."}), 400

    final_prompt = build_prompt_only_marketing_prompt(user_prompt)

    try:
        resp = client.images.generate(
            model=DEPLOYMENT,
            prompt=final_prompt,
            n=1,
            size=PROMPT_ONLY_DEFAULT_SIZE,
            quality="low",
        )
        return jsonify(
            {
                "image": resp.data[0].b64_json,
                "size": PROMPT_ONLY_DEFAULT_SIZE,
                "prompt": final_prompt,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000, use_reloader=False)
