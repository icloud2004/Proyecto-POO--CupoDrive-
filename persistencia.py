import json
import os
import tempfile
from typing import Any, List

# Directorio donde guardaremos los JSON (se crea automáticamente)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

ASPIRANTES_PATH = os.path.join(DATA_DIR, "aspirantes.json")
CUPOS_PATH = os.path.join(DATA_DIR, "cupos.json")

def _save_json_atomic(path: str, obj: Any) -> None:
    """Guarda JSON de forma atómica (temp + replace)."""
    dirn = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile("w", delete=False, dir=dirn, encoding="utf-8") as tf:
        json.dump(obj, tf, ensure_ascii=False, indent=2)
        tmpname = tf.name
    os.replace(tmpname, path)

def _load_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception:
        # Si hay error de parseo devolvemos None
        return None

# ---------------------------
# Aspirantes
# ---------------------------
def serialize_aspirante(a) -> dict:
    """
    Convierte un aspirante (objeto o dict) en dict plano con campos clave.
    Campos: cedula, nombre, puntaje, estado
    """
    if a is None:
        return {"cedula": "", "nombre": "", "puntaje": "", "estado": ""}
    if isinstance(a, dict):
        ced = a.get("identificiacion") or a.get("identificacion") or a.get("cedula") or a.get("ident") or ""
        nombre = (a.get("nombres") or a.get("nombre") or "").strip()
        puntaje = a.get("puntaje_postulacion") or a.get("puntaje") or a.get("puntaje_post") or ""
        estado = a.get("estado") or ""
    else:
        ced = getattr(a, "cedula", "") or getattr(a, "identificiacion", "") or getattr(a, "identificacion", "")
        nombre = getattr(a, "nombre", "") or ""
        puntaje = getattr(a, "puntaje", "")
        estado = getattr(a, "estado", "")
    return {"cedula": str(ced or ""), "nombre": nombre or "", "puntaje": puntaje, "estado": estado or ""}

def serialize_aspirantes_list(aspirantes_list: List) -> List[dict]:
    return [serialize_aspirante(a) for a in aspirantes_list]

def save_aspirantes(aspirantes_list: List, path: str = ASPIRANTES_PATH) -> None:
    data = serialize_aspirantes_list(aspirantes_list)
    _save_json_atomic(path, data)

def load_aspirantes(path: str = ASPIRANTES_PATH) -> List[dict]:
    data = _load_json(path)
    return data or []

# ---------------------------
# Cupos
# ---------------------------
def serialize_cupo(cupo, carrera=None) -> dict:
    """
    Representación mínima de un cupo:
    { carrera_id, carrera_nombre, id_cupo, estado, aspirante_cedula }
    Acepta cupo como objeto o dict; carrera como objeto o dict.
    """
    if cupo is None:
        return {"carrera_id": "", "carrera_nombre": "", "id_cupo": "", "estado": "", "aspirante_cedula": ""}

    # id_cupo
    if isinstance(cupo, dict):
        id_cupo = cupo.get("id_cupo") or cupo.get("id") or ""
        estado = cupo.get("estado") or ""
        aspir_obj = cupo.get("aspirante")
    else:
        id_cupo = getattr(cupo, "id_cupo", "") or getattr(cupo, "id", "")
        estado = getattr(cupo, "estado", "")
        aspir_obj = getattr(cupo, "aspirante", None)

    # aspirante cedula
    aspir_ced = ""
    if aspir_obj:
        if isinstance(aspir_obj, dict):
            aspir_ced = aspir_obj.get("cedula") or aspir_obj.get("identificacion") or aspir_obj.get("identificiacion") or ""
        else:
            aspir_ced = getattr(aspir_obj, "cedula", "") or ""

    # carrera info
    carrera_id = ""
    carrera_nombre = ""
    if carrera is not None:
        if isinstance(carrera, dict):
            carrera_id = carrera.get("id_carrera") or carrera.get("id") or ""
            carrera_nombre = carrera.get("nombre") or ""
        else:
            carrera_id = getattr(carrera, "id_carrera", "") or getattr(carrera, "id", "")
            carrera_nombre = getattr(carrera, "nombre", "")

    return {
        "carrera_id": str(carrera_id or ""),
        "carrera_nombre": carrera_nombre or "",
        "id_cupo": str(id_cupo or ""),
        "estado": estado or "",
        "aspirante_cedula": str(aspir_ced or "")
    }

def serialize_cupos_from_carreras(carreras_list: List) -> List[dict]:
    out = []
    for c in carreras_list:
        for cup in getattr(c, "cupos", []):
            out.append(serialize_cupo(cup, carrera=c))
    return out

def save_cupos(carreras_list: List, path: str = CUPOS_PATH) -> None:
    data = serialize_cupos_from_carreras(carreras_list)
    _save_json_atomic(path, data)

def load_cupos(path: str = CUPOS_PATH) -> List[dict]:
    data = _load_json(path)
    return data or []

def save_cupos_from_records(records: List[dict], path: str = CUPOS_PATH) -> None:
    """Guarda directamente una lista de registros (cuando no se tiene la estructura de carreras)."""
    _save_json_atomic(path, records)