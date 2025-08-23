# -*- coding: utf-8 -*-
from pathlib import Path
import yaml

def load_thresholds() -> dict:
    cfg_path = Path(__file__).with_name("thresholds.yaml")
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
