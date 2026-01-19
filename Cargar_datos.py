

import csv

SEGMENTO_MAP = {
    "1": "Población general",
    "2": "Política de cuotas",
    "3": "Vulnerabilidad socioeconómica",
    "4": "Mérito académico",
    "5": "Bachilleres",
}

def _safe_str(x) -> str:
    try:
        return ("" if x is None else str(x)).strip()
    except Exception:
        return ""

def _safe_int(x, default=0) -> int:
    try:
        s = _safe_str(x)
        return int(s) if s != "" else default
    except Exception:
        return default

def _safe_float(x, default=0.0) -> float:
    try:
        s = _safe_str(x).replace(",", ".")
        return float(s) if s != "" else default
    except Exception:
        return default

def _normalize_row_keys(row: dict) -> dict:
    out = {}
    for k, v in (row or {}).items():
        nk = _safe_str(k).lower()
        out[nk] = v
    return out

def _pick(row: dict, *keys, default=""):
    for k in keys:
        kk = _safe_str(k).lower()
        v = row.get(kk, None)
        if v is None:
            continue
        sv = _safe_str(v)
        if sv != "":
            return sv
    return default

def _detect_delimiter(path: str) -> str:
    # Detecta TAB si el header contiene '\t', caso contrario ';'
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            head = f.readline()
            if "\t" in head:
                return "\t"
    except Exception:
        pass
    return ";"

class Cargar_datos:
    def __init__(self, ruta_csv: str):
        self.ruta_csv = ruta_csv

    def cargar(self):
        aspirantes = []
        seen = set()

        delimiter = _detect_delimiter(self.ruta_csv)

        with open(self.ruta_csv, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)

            for raw in reader:
                row = _normalize_row_keys(raw)

                # ✅ Tu CSV ahora usa 'identificacion'
                cedula = _pick(row, "identificacion", "identificiacion", "cedula", "ident", "id")
                cedula = _safe_str(cedula)

                if cedula == "":
                    continue
                if cedula in seen:
                    continue
                seen.add(cedula)

                nombres = _pick(row, "nombres", "nombre")
                apellidos = _pick(row, "apellidos", "apellido")
                nombre_full = f"{nombres} {apellidos}".strip()

                puntaje = _safe_float(_pick(row, "puntaje_postulacion", "puntaje", "puntaje_post"), 0.0)

                # estado de postulación
                estado = _pick(row, "estado", default="Postulado")
                estado = _safe_str(estado)
                if estado == "":
                    estado = "Postulado"

                # prioridad
                prioridad = _safe_int(_pick(row, "prioridad", default="0"), 0)

                # segmento numérico -> texto
                seg_raw = _pick(row, "segmento", default="1")
                seg_raw = _safe_str(seg_raw)
                segmento_txt = SEGMENTO_MAP.get(seg_raw, "Población general")

                # carrera y campus
                carrera_postulada = _pick(row, "nombre_carrera", "carrera_postulada", "carrera", default="")
                campus = _pick(row, "campus", "can_nombre", "sede", default="")

                aspirante = {
                    "cedula": cedula,
                    "nombre": nombre_full,
                    "puntaje": puntaje,
                    "estado": estado,

                    # ✅ claves para la asignación por segmento
                    "segmento": segmento_txt,
                    "prioridad": prioridad,
                    "carrera_postulada": carrera_postulada,
                    "campus": campus,

                    # extras
                    "tipo_cupo": _pick(row, "tipo_cupo", default=""),
                    "modalidad": _pick(row, "modalidad", default=""),
                    "nivel": _pick(row, "nivel", default=""),
                    "jornada": _pick(row, "jornada", default=""),
                    "acepta_estado": _pick(row, "acepta_estado", default=""),
                    "fecha_acepta_cupo": _pick(row, "feha_acepta_cupo", "fecha_acepta_cupo", default=""),
                }

                aspirantes.append(aspirante)

        # orden estable: prioridad asc, puntaje desc
        try:
            aspirantes.sort(key=lambda a: (int(a.get("prioridad", 0)), -float(a.get("puntaje", 0.0))))
        except Exception:
            pass

        return aspirantes
