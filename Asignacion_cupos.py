#PATRON DE DISEEÑO: STRATEGY

from abc import ABC, abstractmethod
import random
from types import SimpleNamespace

# --------------------------
# Helpers dict/objeto
# --------------------------
def _get_score(a):
    try:
        if isinstance(a, dict):
            return float(a.get("puntaje_postulacion") or a.get("puntaje") or a.get("puntaje_post") or 0)
        return float(getattr(a, "puntaje", 0) or getattr(a, "puntaje_postulacion", 0) or 0)
    except Exception:
        return 0.0

def _get_cedula(a):
    try:
        if isinstance(a, dict):
            return str(a.get("identificiacion") or a.get("identificacion") or a.get("cedula") or a.get("id") or "")
        return str(getattr(a, "cedula", "") or getattr(a, "identificacion", "") or getattr(a, "id", "") or "")
    except Exception:
        return ""

def _stable_sort(candidates):
    try:
        return sorted(candidates, key=lambda x: (-_get_score(x), _get_cedula(x)))
    except Exception:
        return list(candidates)

def _postulados_para_carrera(carrera, aspirantes):
    out = []
    carrera_nombre = (getattr(carrera, "nombre", "") or getattr(carrera, "nombre_carrera", "")).strip().lower()
    campus_carrera = getattr(carrera, "campus", None) or getattr(carrera, "sede", None)

    for a in aspirantes:
        try:
            estado = (a.get("estado") if isinstance(a, dict) else getattr(a, "estado", None))
            if estado is None or str(estado).strip().lower() not in ("postulado", "postulacion", "inscrito"):
                continue

            asp_carrera_val = None
            if isinstance(a, dict):
                asp_carrera_val = a.get("carrera_postulada") or a.get("nombre_carrera") or a.get("carrera")
            else:
                asp_carrera_val = getattr(a, "carrera_postulada", None) or getattr(a, "nombre_carrera", None) or getattr(a, "carrera", None)

            if asp_carrera_val:
                if carrera_nombre and str(asp_carrera_val).strip().lower() != carrera_nombre:
                    continue

            if campus_carrera:
                if isinstance(a, dict):
                    campus_asp = a.get("campus") or a.get("CAN_NOMBRE") or ""
                else:
                    campus_asp = getattr(a, "campus", None) or getattr(a, "sede", None) or ""
                if campus_asp is None or str(campus_asp).strip().lower() != str(campus_carrera).strip().lower():
                    continue

            out.append(a)
        except Exception:
            continue
    return out

def _asignar_a_lista(cupos, aspirantes_seleccionados, carrera):
    asignados = []
    for cupo, aspirante in zip(cupos, aspirantes_seleccionados):
        try:
            if hasattr(cupo, "asignar_aspirante"):
                cupo.asignar_aspirante(aspirante)
            else:
                setattr(cupo, "aspirante", aspirante)
                setattr(cupo, "estado", "Asignado")
        except Exception:
            try:
                cupo.aspirante = aspirante
                cupo.estado = "Asignado"
            except Exception:
                pass

        try:
            if isinstance(aspirante, dict):
                aspirante["carrera_asignada"] = getattr(carrera, "nombre", "")
                aspirante["estado"] = "Asignado"
            else:
                setattr(aspirante, "carrera_asignada", getattr(carrera, "nombre", ""))
                setattr(aspirante, "estado", "Asignado")
        except Exception:
            pass

        asignados.append(aspirante)
    return asignados

# --------------------------
# Strategy interface
# --------------------------
class AssignmentStrategy(ABC):
    @abstractmethod
    def assign(self, carrera, aspirantes):
        raise NotImplementedError()

# --------------------------
# MultiSegmentStrategy (FIX)
# --------------------------
class MultiSegmentStrategy(AssignmentStrategy):
    def __init__(self, tie_breaker: str = "stable", random_seed: int = 42, strict_segments: bool = True):
        """
        strict_segments=True:
          - Si el aspirante tiene segmento pero NO coincide con ningún segmento configurado,
            entonces NO participa (NO se manda a población general).
        """
        self.tie_breaker = tie_breaker
        self.random_seed = random_seed
        self.strict_segments = strict_segments
        if tie_breaker == "random":
            random.seed(random_seed)

    def assign(self, carrera, aspirantes):
        cupos = [c for c in getattr(carrera, "cupos", []) if getattr(c, "estado", "") == "Disponible"]
        total_slots = len(cupos)
        if total_slots == 0:
            return []

        oferta_total = int(getattr(carrera, "oferta_cupos", total_slots))

        # segmentos ordenados
        try:
            segmentos = carrera.obtener_segmentos_ordenados()
        except Exception:
            segmentos = sorted(getattr(carrera, "segmentos", []) or [], key=lambda s: int(getattr(s, "orden", 100)))

        # si no hay segmentos, usar población general 100
        if not segmentos:
            segmentos = [SimpleNamespace(nombre="Población general", porcentaje=100.0, orden=999)]

        # normalización nombre -> original
        norm_to_original = {}
        for s in segmentos:
            original = getattr(s, "nombre", "") or ""
            norm_to_original[original.strip().lower()] = original

        # cuotas por segmento
        cuotas = []
        acc = 0
        for s in segmentos:
            pct = float(getattr(s, "porcentaje", 0.0) or 0.0)
            n = int(round(oferta_total * (pct / 100.0)))
            cuotas.append(n)
            acc += n

        diff = oferta_total - acc
        if diff != 0:
            # ajuste al último segmento
            cuotas[-1] += diff

        postulados = _postulados_para_carrera(carrera, aspirantes)

        # obtener memberships del aspirante (solo texto)
        def aspirante_memberships(asp):
            if isinstance(asp, dict):
                v = asp.get("segmento") or asp.get("grupo") or asp.get("grupo_nombre")
            else:
                v = getattr(asp, "segmento", None) or getattr(asp, "grupo", None) or getattr(asp, "grupo_nombre", None)

            if v is None:
                return []

            # si viene lista
            if isinstance(v, list):
                return [str(x).strip().lower() for x in v if str(x).strip()]

            # si viene string con separadores
            s = str(v).strip()
            if not s:
                return []
            if "," in s or ";" in s:
                parts = [p.strip() for p in s.replace(";", ",").split(",") if p.strip()]
                return [p.lower() for p in parts]

            return [s.lower()]

        # pools por segmento
        candidates_per_segment = {getattr(s, "nombre", ""): [] for s in segmentos}

        for a in postulados:
            memberships = aspirante_memberships(a)  # <- solo lo que trae el aspirante
            chosen_norm = None

            for s in segmentos:
                seg_norm = (getattr(s, "nombre", "") or "").strip().lower()
                if seg_norm in memberships:
                    chosen_norm = seg_norm
                    break

            if chosen_norm is None:
                #  CAMBIO CLAVE:
                # si strict=True y el aspirante TIENE memberships, NO lo mandes a población general
                if self.strict_segments and memberships:
                    continue
                # si NO tiene segmento declarado, entonces sí cae a población general
                chosen_norm = "población general"

            chosen_original = norm_to_original.get(chosen_norm, None)
            if chosen_original is None:
                # si el segmento "población general" no existe en la config, no participa
                continue

            candidates_per_segment.setdefault(chosen_original, []).append(a)

        # ordenar pools
        for k in list(candidates_per_segment.keys()):
            candidates_per_segment[k] = _stable_sort(candidates_per_segment[k])

        assigned = []
        idx = 0

        # asignar por segmentos
        for i, s in enumerate(segmentos):
            cuota = int(cuotas[i] if i < len(cuotas) else 0)
            if cuota <= 0:
                continue
            seg_name = getattr(s, "nombre", "")
            pool = candidates_per_segment.get(seg_name, [])
            take = min(cuota, len(pool), len(cupos) - idx)
            if take > 0:
                sel = pool[:take]
                assigned.extend(_asignar_a_lista(cupos[idx:idx+take], sel, carrera))
                idx += take

        #  IMPORTANTE:
        # NO rellenamos con "cualquier candidato". Solo queda vacío si no hay elegibles.
        return assigned

# --------------------------
# Wrapper esperado por app_web.py
# --------------------------
class Asignacion_cupo:
    def __init__(self, carrera, aspirantes, strategy):
        self.carrera = carrera
        self.aspirantes = aspirantes
        if isinstance(strategy, type):
            try:
                self.strategy = strategy()
            except Exception:
                self.strategy = strategy
        else:
            self.strategy = strategy

    def asignar_cupos(self):
        if self.strategy is None:
            return []
        if hasattr(self.strategy, "assign"):
            return self.strategy.assign(self.carrera, self.aspirantes)
        if hasattr(self.strategy, "asignar"):
            return self.strategy.asignar(self.carrera, self.aspirantes)
        return []

__all__ = ["AssignmentStrategy", "MultiSegmentStrategy", "Asignacion_cupo"]
