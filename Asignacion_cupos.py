
from abc import ABC, abstractmethod
import math
from typing import List
import random

# ------------------------
# HELPERS (compatibles con estructuras dict/objeto)
# ------------------------
def _get_score(a):
    try:
        if isinstance(a, dict):
            return float(a.get("puntaje_postulacion") or a.get("puntaje") or 0)
        return float(getattr(a, "puntaje", 0))
    except Exception:
        return 0.0

def _get_cedula(a):
    try:
        if isinstance(a, dict):
            return str(a.get("identificiacion") or a.get("identificacion") or a.get("cedula") or "")
        return str(getattr(a, "cedula", "") or "")
    except Exception:
        return ""

def _stable_sort(candidates):
    """
    Ordena candidatos por puntaje DESC; tie-breaker por cédula ASC (determinista).
    """
    return sorted(candidates, key=lambda x: (-_get_score(x), _get_cedula(x)))

def _postulados_para_carrera(carrera, aspirantes):
    """
    Filtra aspirantes 'Postulado' y por campus si carrera.campus existe.
    Normaliza 'postulado' case-insensitive.
    """
    out = []
    campus_carrera = getattr(carrera, "campus", None) or getattr(carrera, "sede", None)
    for a in aspirantes:
        try:
            estado = (a.get("estado") if isinstance(a, dict) else getattr(a, "estado", None))
            if estado is None or str(estado).strip().lower() not in ("postulado", "postulacion", "postulado"):
                # aceptar varias formas 'postulado' / 'Postulado'
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
                aspirante["carrera_asignada"] = getattr(carrera, "nombre", carrera)
                aspirante["estado"] = "Asignado"
            else:
                setattr(aspirante, "carrera_asignada", getattr(carrera, "nombre", carrera))
                setattr(aspirante, "estado", "Asignado")
        except Exception:
            pass
        asignados.append(aspirante)
    return asignados

# ------------------------
# INTERFAZ STRATEGY
# ------------------------
class AssignmentStrategy(ABC):
    @abstractmethod
    def assign(self, carrera, aspirantes):
        """Devuelve lista de aspirantes asignados (y realiza la asignación en objetos Cupo)."""
        pass

# ------------------------
# Estrategia multi-segmentos
# ------------------------
class MultiSegmentStrategy(AssignmentStrategy):
    """
    Asigna cupos por segmentos según porcentajes configurados en la carrera.
    Implementación robusta y determinista por defecto.
    """
    def __init__(self, tie_breaker: str = "stable", random_seed: int = 42):
        self.tie_breaker = tie_breaker
        self.random_seed = random_seed
        if tie_breaker == "random":
            random.seed(random_seed)

    def assign(self, carrera, aspirantes):
        cupos = [c for c in getattr(carrera, "cupos", []) if getattr(c, "estado", "") == "Disponible"]
        total_slots = len(cupos)
        if total_slots == 0:
            return []

        oferta_total = int(getattr(carrera, "oferta_cupos", total_slots))

        # obtener segmentos ordenados (si la carrera no tiene implementado obtener_segmentos_ordenados,
        # asumimos que carrera.segmentos es una lista de objetos con .nombre y .porcentaje)
        segmentos = []
        try:
            segmentos = carrera.obtener_segmentos_ordenados()
        except Exception:
            segmentos = sorted(getattr(carrera, "segmentos", []) or [], key=lambda s: int(getattr(s, "orden", 100)))

        # si no hay segmentos definidos, crear default: Población general 100%
        if not segmentos:
            from types import SimpleNamespace
            segmentos = [SimpleNamespace(nombre="Población general", porcentaje=100.0, orden=999)]

        # normalizar porcentajes
        suma_pct = sum([float(getattr(s, "porcentaje", 0.0) or 0.0) for s in segmentos])
        if suma_pct <= 0:
            from types import SimpleNamespace
            segmentos = [SimpleNamespace(nombre="Población general", porcentaje=100.0, orden=999)]

        # calcular cupos por segmento (round y ajustar)
        cuotas = []
        acc = 0
        for s in segmentos:
            n = int(round(oferta_total * (float(getattr(s, "porcentaje", 0.0) or 0.0) / 100.0)))
            cuotas.append(n)
            acc += n
        diff = oferta_total - acc
        if diff != 0:
            # preferir Población general
            idx_pop = None
            for i, s in enumerate(segmentos):
                if getattr(s, "nombre", "").strip().lower().startswith("pobl"):
                    idx_pop = i
                    break
            if idx_pop is None:
                cuotas[-1] += diff
            else:
                cuotas[idx_pop] += diff

        # postulados de la carrera
        postulados = _postulados_para_carrera(carrera, aspirantes)

        # determinar pertenencias (usar campos 'segmentos' o 'segmento' del aspirante si existen)
        def aspirante_segment_members(asp):
            segs = []
            if isinstance(asp, dict):
                if "segmentos" in asp and isinstance(asp["segmentos"], list):
                    segs = [str(x).strip() for x in asp["segmentos"] if x]
                else:
                    val = str(asp.get("segmento") or "").strip()
                    if val:
                        segs = [val]
            else:
                val = getattr(asp, "segmentos", None)
                if isinstance(val, list):
                    segs = [str(x).strip() for x in val if x]
                else:
                    v2 = getattr(asp, "segmento", None)
                    if v2 is not None:
                        segs = [str(v2).strip()]
            if not segs:
                return ["Población general"]
            return segs

        # elegir segmento inicial para cada aspirante (el que tenga menor orden)
        aspirante_chosen_segment = {}
        for a in postulados:
            memberships = aspirante_segment_members(a)
            chosen = None
            for s in segmentos:
                if getattr(s, "nombre", "") in memberships or getattr(s, "nombre", "").strip().lower() in [m.strip().lower() for m in memberships]:
                    chosen = getattr(s, "nombre", "")
                    break
            if not chosen:
                chosen = "Población general"
            key = a if isinstance(a, dict) else id(a)
            aspirante_chosen_segment[key] = chosen

        # construir pools por segmento
        candidates_per_segment = {getattr(s, "nombre", ""): [] for s in segmentos}
        for a in postulados:
            key = a if isinstance(a, dict) else id(a)
            chosen = aspirante_chosen_segment.get(key)
            if chosen not in candidates_per_segment:
                candidates_per_segment.setdefault("Población general", []).append(a)
            else:
                candidates_per_segment[chosen].append(a)

        # ordenar pools
        for k in list(candidates_per_segment.keys()):
            candidates_per_segment[k] = _stable_sort(candidates_per_segment[k])

        assigned = []
        idx = 0

        # asignar por segmentos en orden
        for i, s in enumerate(segmentos):
            cuota = int(cuotas[i] if i < len(cuotas) else 0)
            if cuota <= 0:
                continue
            pool = candidates_per_segment.get(getattr(s, "nombre", ""), [])
            take = min(cuota, len(pool), len(cupos) - idx)
            if take > 0:
                sel = pool[:take]
                assigned_local = _asignar_a_lista(cupos[idx:idx+take], sel, carrera)
                assigned.extend(assigned_local)
                idx += take
            # si faltan postulantes en pool, los cupos se liberan para población general

        # rellenar cupos restantes con población general (incluye candidatos no asignados)
        remaining_slots = len(cupos) - idx
        if remaining_slots > 0:
            already_assigned_keys = set()
            for a in assigned:
                k = _get_cedula(a) or (id(a) if not isinstance(a, dict) else id(a))
                already_assigned_keys.add(k)

            pop_pool = []
            for k, pool in candidates_per_segment.items():
                for a in pool:
                    key = _get_cedula(a) or (id(a) if not isinstance(a, dict) else id(a))
                    if key not in already_assigned_keys:
                        pop_pool.append(a)

            pop_pool = _stable_sort(pop_pool)
            take = min(remaining_slots, len(pop_pool))
            if take > 0:
                sel = pop_pool[:take]
                assigned_local = _asignar_a_lista(cupos[idx:idx+take], sel, carrera)
                assigned.extend(assigned_local)
                idx += take

        return assigned

# ------------------------
# WRAPPER Asignacion_cupo
# ------------------------
class Asignacion_cupo:
    """
    Wrapper que proporciona el método asignar_cupos() que espera app_web.py.
    Recibe: carrera, aspirantes (lista), strategy (instancia de AssignmentStrategy o clase).
    """
    def __init__(self, carrera, aspirantes, strategy):
        self.carrera = carrera
        self.aspirantes = aspirantes
        # strategy puede ser clase o instancia
        if isinstance(strategy, type):
            # instanciar si se pasa la clase
            try:
                self.strategy = strategy()
            except Exception:
                # fallback: intentar instanciar sin args
                self.strategy = strategy
        else:
            self.strategy = strategy

    def asignar_cupos(self):
        if self.strategy is None:
            return []
        # si la estrategia tiene método assign, usarlo
        if hasattr(self.strategy, "assign"):
            return self.strategy.assign(self.carrera, self.aspirantes)
        # si la estrategia usa otro nombre, intentar otros contratos
        if hasattr(self.strategy, "asignar"):
            return self.strategy.asignar(self.carrera, self.aspirantes)
        # no hay método conocido
        return []

# ------------------------
# Exports (nombres públicos)
# ------------------------
__all__ = [
    "AssignmentStrategy",
    "MultiSegmentStrategy",
    "Asignacion_cupo",
]