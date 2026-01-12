import json
import os
import tempfile
from typing import Dict, Any

SEGMENTS_PATH = os.path.join(os.path.dirname(__file__), "data", "segments.json")

def load_segments_config() -> Dict[str, Any]:
    try:
        with open(SEGMENTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

def save_segments_config(cfg: Dict[str, Any]) -> None:
    dirn = os.path.dirname(SEGMENTS_PATH)
    os.makedirs(dirn, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=dirn, encoding="utf-8") as tf:
        json.dump(cfg, tf, ensure_ascii=False, indent=2)
        tmpname = tf.name
    os.replace(tmpname, SEGMENTS_PATH)
