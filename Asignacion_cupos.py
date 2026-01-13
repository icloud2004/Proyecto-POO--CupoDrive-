"""
Módulo de asignación de cupos — versión robusta y compatible con app_web.py

Exporta:
- Asignacion_cupo: wrapper con método asignar_cupos()
- MultiSegmentStrategy: estrategia que implementa la lógica por segmentos

Diseñado para ser tolerante a aspirantes representados como dicts u objetos,
y a carreras que tengan o no la propiedad .segmentos.
"""
from abc import ABC, abstractmethod
import math
import random
from types import SimpleNamespace

# Helpers (compatibles con dict/objeto)
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
    """
    Ordena por puntaje DESC y cédula ASC (determinista).
    """
    try:
        return sorted(candidates, key=lambda x: (-_get_score(x), _get_cedula(x)))
    except Exception:
        # fallback a orden original si ocurre algo raro
        return list(candidates)

def _postulados_para_carrera(carrera, aspirantes):
    """
    Filtra aspirantes con estado 'Postulado' (case-insensitive).
    Si carrera tiene campus/sede, filtra por campus si está presente en el aspirante.
    """
    out = []
    campus_carrera = getattr(carrera, "campus", None) or getattr(carrera, "sede", None)
    for a in aspirantes:
        try:
            estado = (a.get("estado") if isinstance(a, dict) else getattr(a, "estado", None))
            if estado is None or str(estado).strip().lower() not in ("postulado", "postulacion", "inscrito", "postulado"):
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
    """
    Asigna aspirantes a los cupos recibidos (lista). Modifica los objetos cupo y aspirante.
    Devuelve lista de aspirantes asignados.
    """
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

# Interfaz Strategy (opcional)
class AssignmentStrategy(ABC):
    @abstractmethod
    def assign(self, carrera, aspirantes):
        pass

# Estrategia multi-segmentos (robusta)
class MultiSegmentStrategy(AssignmentStrategy):
    def __init__(self, tie_breaker: str = "stable", random_seed: int = 42):
        self.tie_breaker = tie_breaker
        self.random_seed = random_seed
        if tie_breaker == "random":
            random.seed(random_seed)

    def assign(self, carrera, aspirantes):
        # obtener cupos disponibles
        cupos = [c for c in getattr(carrera, "cupos", []) if getattr(c, "estado", "") == "Disponible"]
        total_slots = len(cupos)
        if total_slots == 0:
            return []

        oferta_total = int(getattr(carrera, "oferta_cupos", total_slots))

        # obtener segmentos ordenados de forma defensiva
        segmentos = []
        try:
            segmentos = carrera.obtener_segmentos_ordenados()
        except Exception:
            # fallback: usar carrera.segmentos o vacío
            segmentos = sorted(getattr(carrera, "segmentos", []) or [], key=lambda s: int(getattr(s, "orden", 100)))

        # si no hay segmentos, crear Población general
        if not segmentos:
            segmentos = [SimpleNamespace(nombre="Población general", porcentaje=100.0, orden=999)]

        # validar/normalizar porcentajes
        suma_pct = 0.0
        for s in segmentos:
            try:
                suma_pct += float(getattr(s, "porcentaje", 0.0) or 0.0)
            except Exception:
                suma_pct += 0.0
        if suma_pct <= 0:
            segmentos = [SimpleNamespace(nombre="Población general", porcentaje=100.0, orden=999)]

        # crear mapa de normalización nombre_normalizado -> nombre_original
        norm_to_original = {}
        for s in segmentos:
            original = getattr(s, "nombre", "") or ""
            norm = original.strip().lower()
            norm_to_original[norm] = original

        # calcular cuotas por segmento (round y ajuste)
        cuotas = []
        acc = 0
        for s in segmentos:
            pct = float(getattr(s, "porcentaje", 0.0) or 0.0)
            n = int(round(oferta_total * (pct / 100.0)))
            cuotas.append(n)
            acc += n
        diff = oferta_total - acc
        if diff != 0:
            # preferir población general
            idx_pop = None
            for i, s in enumerate(segmentos):
                if getattr(s, "nombre", "").strip().lower().startswith("pobl"):
                    idx_pop = i
                    break
            if idx_pop is None:
                cuotas[-1] += diff
            else:
                cuotas[idx_pop] += diff

        # candidatos postulados para la carrera
        postulados = _postulados_para_carrera(carrera, aspirantes)

        # mapear pertenencia de aspirantes a segmentos (si no tiene -> Población general)
        def aspirante_segment_members(asp):
            """
            Devuelve lista de memberships normalizados (lower stripped).
            Acepta dict u objeto. También revisa 'grupo' (campo que se usa en Cargar_datos)
            y algunas variantes de nombre común.
            """
            segs = []

            def _normalize_list(lst):
                out = []
                for x in lst:
                    if x is None:
                        continue
                    s = str(x).strip()
                    if s == "":
                        continue
                    out.append(s)
                return out

            if isinstance(asp, dict):
                # prioridades: 'segmentos' (lista), 'segmento', 'grupo'
                if "segmentos" in asp and isinstance(asp["segmentos"], list):
                    segs = _normalize_list(asp["segmentos"])
                else:
                    v = asp.get("segmento") or asp.get("grupo") or asp.get("grupo_nombre") or asp.get("grup")
                    if v:
                        # si viene con separador posible, intentar split
                        if isinstance(v, str) and ("," in v or ";" in v):
                            parts = [p.strip() for p in v.replace(";", ",").split(",") if p.strip()]
                            segs = _normalize_list(parts)
                        else:
                            segs = [str(v).strip()]
            else:
                # objeto: chequeamos atributos comunes
                v = getattr(asp, "segmentos", None)
                if isinstance(v, list):
                    segs = _normalize_list(v)
                else:
                    v2 = getattr(asp, "segmento", None) or getattr(asp, "grupo", None) or getattr(asp, "grupo_nombre", None)
                    if v2:
                        if isinstance(v2, str) and ("," in v2 or ";" in v2):
                            parts = [p.strip() for p in v2.replace(";", ",").split(",") if p.strip()]
                            segs = _normalize_list(parts)
                        else:
                            segs = [str(v2).strip()]

            # Normalizar a lower para comparaciones
            segs_norm = [s.strip().lower() for s in segs if s and str(s).strip() != ""]
            if not segs_norm:
                return ["población general"]
            return segs_norm

        # seleccionar segmento inicial (el de menor orden que coincida)
        aspirante_chosen_segment = {}
        for a in postulados:
            memberships = aspirante_segment_members(a)  # ya normalizados lower
            chosen_norm = None
            for s in segmentos:
                nombre_s = getattr(s, "nombre", "") or ""
                nombre_s_norm = nombre_s.strip().lower()
                # comparar normalizados
                if nombre_s_norm in memberships:
                    chosen_norm = nombre_s_norm
                    break
                # también comparar el original si memberships contienen textos no normalizados
                if nombre_s in memberships:
                    chosen_norm = nombre_s_norm
                    break
            if not chosen_norm:
                chosen_norm = "población general"
            key = a if isinstance(a, dict) else id(a)
            aspirante_chosen_segment[key] = chosen_norm

        # construir pools por segmento (usar nombres originales como claves)
        candidates_per_segment = {getattr(s, "nombre", ""): [] for s in segmentos}
        # asegurar existencia de 'Población general' clave si no existe
        if "Población general" not in candidates_per_segment:
            candidates_per_segment.setdefault("Población general", [])

        for a in postulados:
            key = a if isinstance(a, dict) else id(a)
            chosen_norm = aspirante_chosen_segment.get(key)
            original_name = norm_to_original.get(chosen_norm, None)
            if original_name is None or original_name not in candidates_per_segment:
                # fallback a Población general
                candidates_per_segment.setdefault("Población general", []).append(a)
            else:
                candidates_per_segment[original_name].append(a)

        # ordenar cada pool
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

        # rellenar restantes con población general y cualquier candidato no asignado
        remaining_slots = len(cupos) - idx
        if remaining_slots > 0:
            already_assigned_keys = set()
            for a in assigned:
                k = _get_cedula(a) or (id(a) if not isinstance(a, dict) else id(a))
                already_assigned_keys.add(k)

            pop_pool = []
            for pool in candidates_per_segment.values():
                for a in pool:
                    k = _get_cedula(a) or (id(a) if not isinstance(a, dict) else id(a))
                    if k not in already_assigned_keys:
                        pop_pool.append(a)

            pop_pool = _stable_sort(pop_pool)
            take = min(remaining_slots, len(pop_pool))
            if take > 0:
                sel = pop_pool[:take]
                assigned_local = _asignar_a_lista(cupos[idx:idx+take], sel, carrera)
                assigned.extend(assigned_local)
                idx += take

        return assigned

# Wrapper que app_web.py espera
class Asignacion_cupo:
    """
    Wrapper: recibe (carrera, aspirantes, strategy) y expone asignar_cupos()
    strategy puede ser clase o instancia con método assign(carrera, aspirantes).
    """
    def __init__(self, carrera, aspirantes, strategy):
        self.carrera = carrera
        self.aspirantes = aspirantes
        # aceptar clase o instancia
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

# Public API
__all__ = ["AssignmentStrategy", "MultiSegmentStrategy", "Asignacion_cupo"]