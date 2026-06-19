"""
FunctionAppV2 (FlexConsumption, Linux) 배포 스크립트
─────────────────────────────────────────────────────
1. 배포 zip 생성 (function_app.py + output/events_detailed_*.json + requirements.txt)
2. Blob Storage 'app-packages' 컨테이너에 업로드
3. Azure Management REST API로 배포 트리거
"""

import glob
import io
import json
import os
import sys
import zipfile
import datetime
import requests

# ─── 설정 ────────────────────────────────────────────────────────────────────
STORAGE_CONN = os.environ.get("STORAGE_CONN", "")
SUBSCRIPTION  = "80aed1b5-83fd-4160-911b-039f86fd7aa5"
RESOURCE_GROUP = "Marketing-Ttok-tti"
FUNCTION_APP   = "Marketing-Ttok-tti-FunctionAppV2"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Step 1: 배포 zip 생성 ────────────────────────────────────────────────────
def build_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # 핵심 파일들
        for fname in ["function_app.py", "requirements.txt", "host.json"]:
            src = os.path.join(BASE_DIR, fname)
            if os.path.exists(src):
                zf.write(src, fname)
                print(f"  ✓ {fname}")

        # scrapers 패키지
        scrapers_dir = os.path.join(BASE_DIR, "scrapers")
        if os.path.isdir(scrapers_dir):
            for root, _, files in os.walk(scrapers_dir):
                for f in files:
                    if f.endswith(".py"):
                        full = os.path.join(root, f)
                        arc  = os.path.relpath(full, BASE_DIR)
                        zf.write(full, arc)
                        print(f"  ✓ {arc}")

        # scrape_details.py, pipeline.py
        for fname in ["scrape_details.py", "pipeline.py"]:
            src = os.path.join(BASE_DIR, fname)
            if os.path.exists(src):
                zf.write(src, fname)
                print(f"  ✓ {fname}")

        # output/ 폴더의 가장 최신 events_detailed_*.json
        output_dir = os.path.join(BASE_DIR, "output")
        detail_files = sorted(glob.glob(os.path.join(output_dir, "events_detailed_*.json")))
        if detail_files:
            latest = detail_files[-1]
            arc_name = "output/" + os.path.basename(latest)
            zf.write(latest, arc_name)
            size_kb = os.path.getsize(latest) // 1024
            print(f"  ✓ {arc_name}  ({size_kb} KB)")

    zip_bytes = buf.getvalue()
    print(f"\n  ZIP 크기: {len(zip_bytes):,} bytes")
    return zip_bytes


# ─── Step 2: Blob Storage 업로드 ─────────────────────────────────────────────
def upload_to_blob(zip_bytes: bytes) -> str:
    from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

    svc = BlobServiceClient.from_connection_string(STORAGE_CONN)

    container_name = "app-packages"
    try:
        svc.create_container(container_name)
        print(f"  컨테이너 생성: {container_name}")
    except Exception:
        print(f"  컨테이너 이미 존재: {container_name}")

    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    blob_name = f"etc_event_scraping_{ts}.zip"

    blob_client = svc.get_blob_client(container=container_name, blob=blob_name)
    blob_client.upload_blob(zip_bytes, overwrite=True)
    print(f"  업로드 완료: {blob_name}")

    # SAS URL 생성 (1시간 유효)
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    account_name = "marketingttokttiv2"
    account_key  = os.environ.get("STORAGE_ACCOUNT_KEY", "")
    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=2),
    )
    sas_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
    print(f"  SAS URL 생성 완료")
    return sas_url


# ─── Step 3: Azure Management REST API로 배포 트리거 ─────────────────────────
def get_access_token() -> str:
    import subprocess
    az_exe = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
    result = subprocess.run(
        [az_exe, "account", "get-access-token", "--resource", "https://management.azure.com/", "-o", "json"],
        capture_output=True, text=True, timeout=30
    )
    token_data = json.loads(result.stdout)
    return token_data["accessToken"]


def trigger_deployment(sas_url: str, access_token: str) -> None:
    """Flex Consumption – onedeploy with remoteUrl JSON body"""
    uri = (
        f"https://management.azure.com/subscriptions/{SUBSCRIPTION}"
        f"/resourceGroups/{RESOURCE_GROUP}"
        f"/providers/Microsoft.Web/sites/{FUNCTION_APP}"
        f"/extensions/onedeploy?api-version=2022-03-01"
    )
    payload = {
        "packageUri": sas_url,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    resp = requests.put(uri, headers=headers, json=payload, timeout=300)
    print(f"  배포 응답: {resp.status_code}")
    if resp.status_code in (200, 201, 202):
        print("  배포 성공!")
    else:
        print(f"  응답: {resp.text[:500]}")


# ─── 대안: onedeploy API (FlexConsumption 지원) ──────────────────────────────
def trigger_onedeploy(zip_bytes: bytes, access_token: str) -> None:
    """onedeploy REST API 직접 zip 전송"""
    uri = (
        f"https://management.azure.com/subscriptions/{SUBSCRIPTION}"
        f"/resourceGroups/{RESOURCE_GROUP}"
        f"/providers/Microsoft.Web/sites/{FUNCTION_APP}"
        f"/extensions/onedeploy?api-version=2022-03-01"
    )
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/zip",
    }
    resp = requests.put(uri, headers=headers, data=zip_bytes, timeout=300)
    print(f"  onedeploy 응답: {resp.status_code}")
    if resp.status_code in (200, 201, 202):
        print("  배포 성공!")
    else:
        print(f"  응답: {resp.text[:500]}")


# ─── 메인 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== FunctionAppV2 배포 시작 ===\n")

    print("[1/3] zip 빌드 중...")
    zip_bytes = build_zip()

    print("\n[2/3] 액세스 토큰 획득...")
    try:
        token = get_access_token()
        print("  토큰 획득 성공")
    except Exception as e:
        print(f"  토큰 획득 실패: {e}")
        sys.exit(1)

    print("\n[3/3] Blob Storage 업로드 후 packageUri 배포...")
    try:
        sas_url = upload_to_blob(zip_bytes)
        trigger_deployment(sas_url, token)
    except Exception as e:
        print(f"  Blob 배포 실패: {e}. onedeploy 시도...")
        trigger_onedeploy(zip_bytes, token)

    print("\n=== 배포 완료 ===")
    print(f"  Function App: https://marketing-ttok-tti-functionappv2-bxayc6f7b4f5fhg0.swedencentral-01.azurewebsites.net/api/etc_event_scraping")
