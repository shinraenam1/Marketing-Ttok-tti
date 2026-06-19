import base64
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT").rstrip("/") + "/openai/v1"
api_key = os.getenv("AZURE_OPENAI_KEY")
deployment_name = "gpt-image-2"

client = OpenAI(
    base_url=endpoint,
    api_key=api_key,
)

print(f"Endpoint: {endpoint}")
print("이미지 생성 중...")

img = client.images.generate(
    model=deployment_name,
    prompt="A cute baby polar bear playing in the snow",
    n=1,
    size="1024x1024",
)

image_bytes = base64.b64decode(img.data[0].b64_json)
output_path = "output.png"
with open(output_path, "wb") as f:
    f.write(image_bytes)

print(f"이미지 저장 완료: {output_path}")
