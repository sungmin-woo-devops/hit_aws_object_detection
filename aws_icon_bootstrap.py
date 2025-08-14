# 목적: 메타 로드 -> 라벨 정규화 -> 템플릿 준비 -> 간단 탐지 실행까지의 최소 골격
# 경로는 필요 시 수정
from pathlib import Path
import json, csv, re
import pandas as pd
import numpy as np
import cv2
from typing import Dict, List, Tuple

# ==== 0) 경로 상수 ============================================================
ROOT = Path("/mnt/data/aws_icon_intake")
META = ROOT / "metadata"
STD_ICONS = ROOT / "standardized/icons"
CLASS_MAP_JSON = META / "class_map.json"
ALIAS_CSV = META / "alias.csv"
INVENTORY_CSV = META / "inventory.csv" 

# ==== 1) 메타 로드 & 유틸 ======================================================
def load_class_map() -> Dict[int, Dict]:
    j = json.load(CLASS_MAP_JSON.read_text(encoding="utf-8"))
    return {c['id']: c for c in j['classes']}

