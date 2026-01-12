from abc import ABC, abstractmethod
import math
from typing import List
import random

# Helpers (compatibles con estructuras dict/objeto)
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

def _stable_sort(candidates, reverse=True):
    # orden por puntaje; tie-breaker por cédula asc (determinista)
    return sorted(candidates, key=lambda x: (_get_score(x), _get_cedula(x)), reverse=reverse)

def _postulados_para_carrera(carrera, aspirantes):
    """
    Filtra aspirantes 'Postulado' y por campus si carrera.campus existe.
    """
    out = []
    campus_carrera = getattr(carrera, "campus", None) or getattr(carrera, "sede", None)
    for a in aspirantes:
        try:
            estado = getattr(a, "estado", None) if not isinstance(a, dict) else a.get("estado")
            if estado is None or str(estado).strip().lower() != "postulado":
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

# Interfaz
class AssignmentStrategy(ABC):
    @abstractmethod
    def assign(self, carrera, aspirantes):
        pass

# Estrategia multi-segmentos
class MultiSegmentStrategy(AssignmentStrategy):
    """
    Asigna cupos por segmentos según porcentajes configurados en la carrera.
    - La carrera debe tener .segmentos: lista de Segmento con .porcentaje y .orden
    - Reglas:
      - Primero ordenar segmentos por .orden asc (1,2,3,...).
      - Para cada segmento calcular cupos = round(oferta_total * porcentaje/100) (ajustes más abajo).
      - Dentro de cada segmento, ordenar postulantes por puntaje (desc) y asignar hasta completar su cuota.
      - Si un postulante pertenece a varios segmentos se considera inicialmente en el segmento con menor orden (el que más le favorezca según política).
      - Si un segmento no consume todos sus cupos (falta de postulantes), los cupos se liberan a Población general.
      - Finalmente, rellenar los cupos restantes con Población general ordenada por puntaje.
    """
    def __init__(self, tie_breaker:str="stable", random_seed:int=42):
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

        # obtener segmentos ordenados
        segmentos = carrera.obtener_segmentos_ordenados()
        # si no hay segmentos definidos, crear default: Población general 100%
        if not segmentos:
            from Segmento import Segmento
            segmentos = [Segmento("Población general", porcentaje=100.0, orden=999)]

        # normalizar porcentajes (garantizar suma 100 si admin lo garantiza)
        suma_pct = sum([float(s.porcentaje or 0.0) for s in segmentos])
        if suma_pct <= 0:
            # fallback: todo a Población general
            segmentos = [type("S", (), {"nombre":"Población general", "porcentaje":100.0, "orden":999})()]

        # calcular cupos por segmento (usamos round, luego ajustamos sobrante)
        cuotas = []
        acc = 0
        for s in segmentos:
            n = int(round(oferta_total * (float(s.porcentaje or 0.0) / 100.0)))
            cuotas.append(n)
            acc += n
        # ajustar diferencia por redondeo
        diff = oferta_total - acc
        if diff != 0:
            # aplicar ajuste al segmento de Población general si existe, si no al último segmento
            idx_pop = None
            for i, s in enumerate(segmentos):
                if s.nombre.strip().lower().startswith("pobl"):
                    idx_pop = i
                    break
            if idx_pop is None:
                # ajustar último segmento
                cuotas[-1] += diff
            else:
                cuotas[idx_pop] += diff

        # Preparar postulantes y asignarles un segmento inicial (el que más les favorezca = menor orden en segmentos que coincida)
        postulados = _postulados_para_carrera(carrera, aspirantes)

        # Determinar pertenencia a segmentos para cada aspirante:
        # - Si el aspirante tiene atributo 'segmentos' (lista de nombres), usamos eso.
        # - Si solo tiene 'segmento' numérico o etiqueta simple, lo mapeamos a nombres existentes si coincide.
        # - En caso contrario lo colocamos en 'Población general'.
        def aspirante_segment_members(asp):
            segs = []
            if isinstance(asp, dict):
                # posible campo 'segmentos' como lista en JSON
                if "segmentos" in asp and isinstance(asp["segmentos"], list):
                    segs = [str(x).strip() for x in asp["segmentos"] if x]
                else:
                    # intentar por 'segmento' numérico -> mapear a nombres si existe campo mapping en asp
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
            # normalizar: si no tiene membership devolvemos ['Población general']
            if not segs:
                return ["Población general"]
            return segs

        # Build a map: aspirante -> chosen_segment_name (the segment with lowest orden among those the aspirant belongs to)
        segment_names_order = [s.nombre for s in segmentos]
        aspirante_chosen_segment = {}
        for a in postulados:
            memberships = aspirante_segment_members(a)
            # choose the segment with smallest index in segment_names_order that is in memberships
            chosen = None
            for s in segmentos:
                if s.nombre in memberships or s.nombre.strip().lower() in [m.strip().lower() for m in memberships]:
                    chosen = s.nombre
                    break
            if not chosen:
                chosen = "Población general"
            aspirante_chosen_segment[a if isinstance(a, dict) else id(a)] = chosen

        # Prepare lists of candidates per segment
        candidates_per_segment = {s.nombre: [] for s in segmentos}
        for a in postulados:
            chosen = aspirante_chosen_segment.get(a if isinstance(a, dict) else id(a))
            if chosen not in candidates_per_segment:
                # if chosen not defined in configured segments, send to Población general bucket
                candidates_per_segment.setdefault("Población general", []).append(a)
            else:
                candidates_per_segment[chosen].append(a)

        # Sort candidates in each segment by puntaje desc (deterministic)
        for k in candidates_per_segment:
            candidates_per_segment[k] = _stable_sort(candidates_per_segment[k], reverse=True)

        assigned = []
        idx = 0

        # Iterate segments in order and fill their quotas
        for i, s in enumerate(segmentos):
            cuota = int(cuotas[i] if i < len(cuotas) else 0)
            if cuota <= 0:
                continue
            pool = candidates_per_segment.get(s.nombre, [])
            take = min(cuota, len(pool), len(cupos) - idx)
            if take > 0:
                sel = pool[:take]
                assigned_local = _asignar_a_lista(cupos[idx:idx+take], sel, carrera)
                assigned.extend(assigned_local)
                idx += take
            # if pool had fewer than cuota, remaining cups will be released to población general implicitly

        # After processing segments, fill remaining slots with Población general (which includes freed cups)
        remaining_slots = len(cupos) - idx
        if remaining_slots > 0:
            # build población general pool: candidates not yet assigned, plus those originally in Población general
            already_assigned_set = set()
            for a in assigned:
                # unify keyed by cedula or id
                key = _get_cedula(a) or (id(a) if not isinstance(a, dict) else id(a))
                already_assigned_set.add(key)

            pop_pool = []
            # candidates who were in 'Población general' bucket
            pop_bucket = candidates_per_segment.get("Población general", [])
            # plus candidates from other buckets who were not assigned (they will be available to general)
            for k, pool in candidates_per_segment.items():
                if k == "Población general":
                    for a in pop_bucket:
                        key = _get_cedula(a) or (id(a) if not isinstance(a, dict) else id(a))
                        if key not in already_assigned_set:
                            pop_pool.append(a)
                else:
                    for a in pool:
                        key = _get_cedula(a) or (id(a) if not isinstance(a, dict) else id(a))
                        if key not in already_assigned_set:
                            pop_pool.append(a)

            # orden stable por puntaje
            pop_pool = _stable_sort(pop_pool, reverse=True)
            take = min(remaining_slots, len(pop_pool))
            if take > 0:
                sel = pop_pool[:take]
                assigned_local = _asignar_a_lista(cupos[idx:idx+take], sel, carrera)
                assigned.extend(assigned_local)
                idx += take

        return assigned