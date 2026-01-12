class Segmento:
    """
    Modelo de segmento con soporte de porcentaje, límites (min/max)
    y criterio de verificación para un aspirante.
    """

    def __init__(self, nombre: str, porcentaje: float = 0.0, criterios=None, min_pct: float = 0.0, max_pct: float = 100.0):
        self.nombre = nombre
        self.porcentaje = float(porcentaje)
        self.criterios = criterios or []
        self.min_pct = float(min_pct)
        self.max_pct = float(max_pct)

    def verificar_criterios(self, aspirante) -> bool:
        """
        Método simplificado para detectar pertenencia según nombre de segmento.
        Puede reemplazarse por un callback más avanzado si se requiere.
        """
        nombre = self.nombre.strip().lower()
        if nombre in ["vulnerabilidad", "grupo de mayor vulnerabilidad", "grupo vulnerable"]:
            # Se espera aspirante.vulnerabilidad con valores tipo "alta", "media", "baja"
            try:
                return getattr(aspirante, "vulnerabilidad", "").strip().lower() == "alta"
            except Exception:
                return False
        elif nombre in ["mérito", "mérito académico", "merito academico", "mérito académico"]:
            try:
                return float(getattr(aspirante, "puntaje", 0)) >= 850
            except Exception:
                return False
        elif nombre in ["política de cuotas", "politica de cuotas", "política cuotas", "política de cuotas"]:
            # Se espera que el aspirante tenga un atributo que lo marque dentro de política de cuotas.
            return getattr(aspirante, "politica_cuotas", False) or getattr(aspirante, "politica", False)
        elif nombre in ["población general", "poblacion general", "población general"]:
            return True
        elif "bachiller" in nombre:
            # Distinción entre pueblos y demás se puede manejar en el nombre del segmento:
            # p. ej. "Bachilleres pueblos" vs "Bachilleres"
            try:
                return getattr(aspirante, "bachiller_ultimo_regimen", False)
            except Exception:
                return False
        else:
            # Otros segmentos que hayan sido creados manualmente: se asume que criterios es lista
            # de funciones o expresiones simples (no se evalúan con eval por seguridad).
            # Si criterios contiene callables, ejecútalos.
            for c in self.criterios:
                if callable(c):
                    try:
                        if c(aspirante):
                            return True
                    except Exception:
                        continue
            return False

    def calcular_cupos_total(self, oferta_total: int) -> int:
        """Calcula cupos destinados a este segmento (redondeo hacia abajo)."""
        try:
            cupos_segmento = int((self.porcentaje / 100.0) * oferta_total)
        except Exception:
            cupos_segmento = 0
        return max(0, cupos_segmento)

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "porcentaje": self.porcentaje,
            "min_pct": self.min_pct,
            "max_pct": self.max_pct,
            "criterios": []  # no serializamos funciones
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            nombre=d.get("nombre", ""),
            porcentaje=d.get("porcentaje", 0.0),
            criterios=d.get("criterios", []),
            min_pct=d.get("min_pct", 0.0),
            max_pct=d.get("max_pct", 100.0)
        )

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje}%)"
