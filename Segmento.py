from typing import Optional
import math

class Segmento:
    """
    Representa un segmento poblacional para la asignación de cupos.
    - nombre: nombre descriptivo (ej. 'Política de cuotas', 'Vulnerabilidad', 'Merito Académico', etc.)
    - porcentaje: porcentaje de la oferta total asignado a este segmento (valor en 0..100)
    - orden: entero que indica el orden en que se ejecuta la asignación (1 = primero)
    - min_pct / max_pct: valores opcionales para limites normativos (0..100)
    - descripcion: texto adicional
    """
    def __init__(self, nombre: str, porcentaje: float = 0.0, orden: int = 100, min_pct: Optional[float]=None, max_pct: Optional[float]=None, descripcion: str = ""):
        self.nombre = (nombre or "").strip()
        self.porcentaje = float(porcentaje or 0.0)
        self.orden = int(orden or 100)
        self.min_pct = float(min_pct) if min_pct is not None else None
        self.max_pct = float(max_pct) if max_pct is not None else None
        self.descripcion = descripcion or ""

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "porcentaje": float(self.porcentaje),
            "orden": int(self.orden),
            "min_pct": None if self.min_pct is None else float(self.min_pct),
            "max_pct": None if self.max_pct is None else float(self.max_pct),
            "descripcion": self.descripcion
        }

    @classmethod
    def from_dict(cls, d):
        if d is None:
            return None
        return cls(
            nombre=d.get("nombre",""),
            porcentaje=float(d.get("porcentaje", 0.0) or 0.0),
            orden=int(d.get("orden", 100) or 100),
            min_pct=d.get("min_pct", None),
            max_pct=d.get("max_pct", None),
            descripcion=d.get("descripcion","")
        )

    def calcular_cupos_total(self, oferta_total: int) -> int:
        """
        Calcula la cantidad de cupos que corresponde a este segmento
        según su porcentaje aplicado sobre oferta_total.
        (Se usa floor para distribución inicial; la redistribución se maneja en la estrategia)
        """
        try:
            return int(math.floor(oferta_total * (float(self.porcentaje or 0.0) / 100.0)))
        except Exception:
            return 0
