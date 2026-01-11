"""
Cargar_carreras.py
Módulo para cargar la oferta de carreras desde 'Carreras.csv' (por defecto).
- Maneja CSV con separador ';' y BOM (utf-8-sig).
- Intenta devolver instancias de la clase Carrera si está disponible en el repo,
  en caso contrario devuelve diccionarios con los campos parseados.
- Tolerante a variaciones en nombres de columna comunes.

Uso:
    from Cargar_carreras import CargarCarreras
    loader = CargarCarreras("Carreras.csv")
    carreras = loader.cargar(as_model=True)  # lista de Carrera o de dicts
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
                return row.get(mapping[key], None)
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
         - o diccionarios con keys: id_carrera, nombre, oferta_cupos, fila_raw
        """
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"No existe el archivo: {self.path}")

        resultados: List[Any] = []

        with open(self.path, newline="", encoding=self.encoding) as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            field_map = self._normalize_fieldnames(reader.fieldnames or [])

            # Candidatos para los campos que nos interesan (variaciones comunes)
            nombre_cands = [
                "car_nombre_carrera", "car_nombre", "ofa_titulo", "pro_nombre", "car_nombre_carrera"
            ]
            oferta_cands = [
                "cus_total_cupos", "cus_total", "cus_cupos_total", "cus_cupos_primer_semestre", "cus_total_cupos"
            ]
            id_cands = [
                "cus_id", "ofa_id", "car_id", "oferta_id", "ies_id"
            ]

            for i, row in enumerate(reader):
                # Extraer valores con tolerancia a cabeceras
                nombre_raw = self._find_value(row, field_map, nombre_cands) or ""
                oferta_raw = self._find_value(row, field_map, oferta_cands)
                id_raw = self._find_value(row, field_map, id_cands)

                nombre = str(nombre_raw).strip()
                oferta = self._to_int(oferta_raw)
                id_carrera = str(id_raw).strip() if id_raw and str(id_raw).strip() != "" else f"auto-{i+1}"

                registro = {
                    "id_carrera": id_carrera,
                    "nombre": nombre or f"Carrera-{i+1}",
                    "oferta_cupos": oferta,
                    "fila_raw": row
                }

                if as_model and _HAS_CARRERA_CLASS:
                    try:
                        # Crear instancia de Carrera con los campos mínimos
                        carrera_obj = Carrera(
                            id_carrera=str(registro["id_carrera"]),
                            nombre=registro["nombre"],
                            oferta_cupos=int(registro["oferta_cupos"] or 0)
                        )
                        resultados.append(carrera_obj)
                    except Exception as e:
                        # Si falla creación, devolver como dict con la razón
                        registro["error_creacion"] = str(e)
                        resultados.append(registro)
                else:
                    resultados.append(registro)

        if as_model and not _HAS_CARRERA_CLASS:
            print("[CargarCarreras] Aviso: la clase Carrera no está disponible; se retornan diccionarios.")

        return resultados


# Ejemplo de uso directo
if __name__ == "__main__":
    loader = CargarCarreras("Carreras.csv")
    try:
        carreras = loader.cargar(as_model=True)
        for c in carreras:
            if _HAS_CARRERA_CLASS and isinstance(c, Carrera):
                print(f"{c.id_carrera} - {c.nombre} ({c.oferta_cupos} cupos)")
            else:
                # dict con información
                print(f"{c.get('id_carrera')} - {c.get('nombre')} ({c.get('oferta_cupos')} cupos)")
    except FileNotFoundError as e:
        print(e)