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
    Convierte un aspirante (objeto o dict) en dict plano.
    IMPORTANTÍSIMO: NO perder campos de segmentación.
    """
    if a is None:
        return {
            "cedula": "", "nombre": "", "puntaje": "", "estado": "",
            "segmento": "", "prioridad": "", "carrera_postulada": "", "campus": ""
        }

    def pick(d, *keys, default=""):
        for k in keys:
            if k in d and d[k] not in (None, ""):
                return d[k]
        return default

    # -----------------------
    # Aspirante como dict
    # -----------------------
    if isinstance(a, dict):
        ced = pick(a, "cedula", "identificacion", "identificiacion", "ident", "id", default="")
        nombre = (pick(a, "nombre", "nombres", default="") or "").strip()

        puntaje = pick(a, "puntaje_postulacion", "puntaje", "puntaje_post", default=0)
        estado = pick(a, "estado", "acepta_estado", default="Postulado")

        #  CAMPOS CLAVE
        segmento = pick(a, "segmento", "grupo", "grupo_nombre", "segmento_slug", default="")
        prioridad = pick(a, "prioridad", "orden_prioridad", default="")
        carrera_post = pick(a, "carrera_postulada", "nombre_carrera", "carrera", "pro_nombre", default="")
        campus = pick(a, "campus", "CAN_NOMBRE", "sede", default="")

        return {
            "cedula": str(ced or ""),
            "nombre": nombre,
            "puntaje": puntaje,
            "estado": estado,
            "segmento": segmento,
            "prioridad": prioridad,
            "carrera_postulada": carrera_post,
            "campus": campus
        }

    # -----------------------
    # Aspirante como objeto
    # -----------------------
    ced = getattr(a, "cedula", "") or getattr(a, "identificacion", "") or getattr(a, "identificiacion", "") or ""
    nombre = (getattr(a, "nombre", "") or getattr(a, "nombres", "") or "").strip()
    puntaje = getattr(a, "puntaje", "") or getattr(a, "puntaje_postulacion", "") or 0
    estado = getattr(a, "estado", "") or "Postulado"

    segmento = (
        getattr(a, "segmento", None)
        or getattr(a, "grupo", None)
        or getattr(a, "grupo_nombre", None)
        or getattr(a, "segmento_slug", None)
        or ""
    )
    prioridad = getattr(a, "prioridad", "") or getattr(a, "orden_prioridad", "") or ""
    carrera_post = (
        getattr(a, "carrera_postulada", None)
        or getattr(a, "nombre_carrera", None)
        or getattr(a, "carrera", None)
        or getattr(a, "pro_nombre", None)
        or ""
    )
    campus = getattr(a, "campus", "") or getattr(a, "CAN_NOMBRE", "") or getattr(a, "sede", "") or ""

    return {
        "cedula": str(ced or ""),
        "nombre": nombre,
        "puntaje": puntaje,
        "estado": estado,
        "segmento": segmento,
        "prioridad": prioridad,
        "carrera_postulada": carrera_post,
        "campus": campus
    }


def serialize_aspirantes_list(aspirantes_list: List) -> List[dict]:
    return [serialize_aspirante(a) for a in aspirantes_list]

def save_aspirantes(aspirantes_list: List, path: str = ASPIRANTES_PATH, dedupe: bool = True) -> None:
    """
    Guarda la lista de aspirantes en JSON. Por defecto elimina duplicados por 'cedula'
    para evitar acumular repetidos si la lista contiene entradas repetidas.
    """
    data = serialize_aspirantes_list(aspirantes_list)

    if dedupe:
        seen = set()
        deduped = []
        for a in data:
            ced = str((a or {}).get("cedula", "")).strip()
            if ced == "":
                # si no hay cédula, lo incluimos igual (o podrías ignorarlo)
                deduped.append(a)
                continue
            if ced in seen:
                continue
            seen.add(ced)
            deduped.append(a)
        data = deduped

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


SEGMENTOS_PATH = os.path.join(DATA_DIR, "segmentos.json")

def save_segmentos(carreras_list: List, path: str = SEGMENTOS_PATH) -> None:
    """
    Guarda estructura de segmentos por carrera:
    [ { "id_carrera": "...", "segmentos": [ {segmento dict}, ... ] }, ... ]
    """
    out = []
    for c in carreras_list:
        segs = []
        for s in getattr(c, "segmentos", []):
            try:
                segs.append(s.to_dict())
            except Exception:
                # si es dict
                segs.append(s if isinstance(s, dict) else {})
        out.append({"id_carrera": getattr(c, "id_carrera", "") or getattr(c, "nombre", ""), "segmentos": segs})
    _save_json_atomic(path, out)

def load_segmentos(path: str = SEGMENTOS_PATH) -> List[dict]:
    data = _load_json(path)
    return data or []