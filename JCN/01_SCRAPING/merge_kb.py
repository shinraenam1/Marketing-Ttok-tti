"""
KB detailed 데이터를 events_detailed에 반영 → 새 events_detailed 저장 → report.html 생성
"""
import json, glob, os, re, sys
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# ─── 1. 파일 로드 ─────────────────────────────────────────────────────────────
# KB 상세 파일 (방금 생성됨)
kb_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "kb_detailed_*.json")))
if not kb_files:
    sys.exit("kb_detailed_*.json 파일 없음")
kb_latest = kb_files[-1]
kb_data = json.load(open(kb_latest, encoding="utf-8"))
print(f"KB 상세: {os.path.basename(kb_latest)} ({len(kb_data)}건)")

# 기존 events_detailed (비-KB 이벤트용)
det_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "events_detailed_*.json")))
if not det_files:
    sys.exit("events_detailed_*.json 파일 없음")
det_latest = det_files[-1]
det_data = json.load(open(det_latest, encoding="utf-8"))
non_kb = [e for e in det_data if e.get("card_company") != "KB국민카드"]
print(f"비-KB: {os.path.basename(det_latest)} ({len(non_kb)}건)")

# ─── 2. 병합 ─────────────────────────────────────────────────────────────────
merged = kb_data + non_kb
print(f"병합 총 {len(merged)}건")

# ─── 3. 저장 ─────────────────────────────────────────────────────────────────
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out_path = os.path.join(OUTPUT_DIR, f"events_detailed_{ts}.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)
print(f"✅ 저장: {os.path.basename(out_path)}")
