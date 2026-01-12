"""
Módulo para cargar la oferta de carreras desde 'Carreras.csv' (por defecto).
- Maneja CSV con separador ';' y BOM (utf-8-sig).
- Intenta devolver instancias de la clase Carrera si está disponible en el repo,
  en caso contrario devuelve diccionarios con los campos parseados.
- Tolerante a variaciones en nombres de columna comunes.
"""

from typing import List, Dict, Any
import csv
import os

# Intentamos importar la clase Carrera del repo; si falla devolvemos dicts
try:
    from Carrera import Carrera  # type: ignore
    _HAS_CARRERA_CLASS = True
except Exception:
    _HAS_CARRERA_CLASS = False


class CargarCarreras:
    def __init__(self, path: str = "Carreras.csv", delimiter: str = ";", encoding: str = "utf-8-sig"):
        self.path = path
        self.delimiter = delimiter
        self.encoding = encoding

    def _normalize_fieldnames(self, fieldnames: List[str]) -> Dict[str, str]:
        """
        Construye un mapa lower->original para búsqueda tolerante.
        """
        mapping = {}
        for fn in (fieldnames or []):
            if fn is None:
                continue
            key = fn.strip().lower()
            mapping[key] = fn
        return mapping

    def _find_value(self, row: Dict[str, str], mapping: Dict[str, str], candidates: List[str]):
        """
        Busca en row un valor para cualquiera de los candidatos (case-insensitive).
        Devuelve None si no encuentra.
        """
        for c in candidates:
            key = c.strip().lower()
            if key in mapping:
                val = row.get(mapping[key], None)
                if val is not None:
                    return val
        return None

    def _to_int(self, value: Any) -> int:
        """
        Intenta convertir a int, devuelve 0 si no es posible o está vacío.
        """
        if value is None:
            return 0
        try:
            s = str(value).strip()
            if s == "":
                return 0
            return int(float(s.replace(",", ".")))
        except Exception:
            return 0

    def cargar(self, as_model: bool = True) -> List[Any]:
        """
        Carga el CSV y devuelve una lista de:
         - instancias Carrera (si as_model True y la clase Carrera está disponible)
         - o diccionarios con keys: id_carrera, nombre, oferta_cupos, campus, fila_raw
        """
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"No existe el archivo: {self.path}")

        resultados: List[Any] = []

        with open(self.path, newline="", encoding=self.encoding) as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            field_map = self._normalize_fieldnames(reader.fieldnames or [])

            # Candidatos para los campos que nos interesan (variaciones comunes)
            nombre_cands = [
                "car_nombre_carrera", "car_nombre", "ofa_titulo", "pro_nombre", "car_nombre"
            ]
            oferta_cands = [
                "cus_total_cupos", "cus_total", "oferta_cupos", "cus_total_cupos", "oferta"
            ]
            id_cands = [
                "cus_id", "ofa_id", "id", "id_carrera"
            ]
            campus_cands = [
                "can_nombre", "campus", "sede", "prq_nombre"
            ]

            for row in reader:
                # extraer campos tolerantes
                nombre = self._find_value(row, field_map, nombre_cands) or row.get(next(iter(row.keys())), "").strip()
                oferta_raw = self._find_value(row, field_map, oferta_cands)
                id_raw = self._find_value(row, field_map, id_cands)
                campus = self._find_value(row, field_map, campus_cands) or ""

                oferta = self._to_int(oferta_raw)
                id_carrera = (id_raw or "").strip()

                # Normalizar nombre y campus
                nombre = (nombre or "").strip()
                campus = (campus or "").strip()

                if as_model and _HAS_CARRERA_CLASS:
                    # intentar crear la instancia Carrera con campus si el constructor lo acepta
                    try:
                        try:
                            carrera_obj = Carrera(id_carrera, nombre, oferta, campus=campus)
                        except TypeError:
                            # fallback: intentar con firma posicional
                            carrera_obj = Carrera(id_carrera, nombre, oferta, None, campus)
                    except Exception:
                        # Si falla crear el objeto, caer al dict fallback
                        carrera_obj = None

                    if carrera_obj is None:
                        resultados.append({
                            "id_carrera": id_carrera,
                            "nombre": nombre,
                            "oferta_cupos": oferta,
                            "campus": campus,
                            "fila_raw": row
                        })
                    else:
                        # si la clase Carrera existe pero no tiene campus asignado, intentar setearlo
                        try:
                            if not getattr(carrera_obj, "campus", None):
                                setattr(carrera_obj, "campus", campus)
                        except Exception:
                            pass
                        resultados.append(carrera_obj)
                else:
                    # devolver dict
                    resultados.append({
                        "id_carrera": id_carrera,
                        "nombre": nombre,
                        "oferta_cupos": oferta,
                        "campus": campus,
                        "fila_raw": row
                    })

        return resultados