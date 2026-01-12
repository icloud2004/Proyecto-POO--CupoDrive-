
# Estrategias y controlador para la asignación de cupos por carrera.
# Contiene: AssignmentStrategy (interfaz), MeritStrategy, LotteryStrategy,
# SegmentQuotaStrategy (implementación custom según reglas de prioridad/segmento/puntaje)
# y la clase Asignacion_cupo que orquesta la asignación usando una estrategia.

from abc import ABC, abstractmethod
import random
import math

# ------------------------
# INTERFAZ STRATEGY
# ------------------------
class AssignmentStrategy(ABC):

    @abstractmethod
    def assign(self, carrera, aspirantes):
        """Devuelve lista de aspirantes asignados (y realiza la asignación en objetos Cupo)."""
        pass

    def resolver_empates(self, empatados, cupos_disponibles):
        """
        Método por defecto.
        Las estrategias pueden sobrescribirlo.
        """
        return empatados[:cupos_disponibles]


# ------------------------
# HELPERS COMUNES
# ------------------------
def _postulados_para_carrera(carrera, aspirantes):
    """
    Devuelve aspirantes que están 'Postulado' y que son elegibles para la carrera.
    Compatibilidad con objetos y dicts.
    Filtra además por campus/sede si la carrera tiene atributo 'campus'.
    """
    out = []
    campus_carrera = getattr(carrera, "campus", None) or getattr(carrera, "sede", None)
    for a in aspirantes:
        try:
            estado = getattr(a, "estado", None) if not isinstance(a, dict) else a.get("estado")
            if estado is None:
                continue
            if str(estado).strip().lower() != "postulado":
                continue

            # Filtrado por campus: si la carrera tiene campus definido, el aspirante debe pertenecer a ese campus
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
    Toma dos listas emparejadas (cupos y aspirantes) y realiza la asignación:
    - llama cupo.asignar_aspirante(aspirante) si existe
    - asigna atributos aspirante.carrera_asignada y aspirante.estado
    Devuelve la lista de aspirantes asignados.
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
# ESTRATEGIAS CONCRETAS
# ------------------------
class MeritStrategy(AssignmentStrategy):
    """
    Asignación por mérito: ordena postulados por puntaje descendente y asigna cupos disponibles.
    Resuelve empates con resolver_empates (por defecto toma los primeros).
    """

    def assign(self, carrera, aspirantes):
        postulados = _postulados_para_carrera(carrera, aspirantes)
        ordenados = sorted(
            postulados,
            key=lambda x: float(getattr(x, "puntaje", 0) if not isinstance(x, dict) else (x.get("puntaje_postulacion") or x.get("puntaje") or 0)),
            reverse=True
        )

        cupos = [c for c in getattr(carrera, "cupos", []) if getattr(c, "estado", "") == "Disponible"]
        asignados = []
        i = 0

        while i < len(ordenados) and len(asignados) < len(cupos):
            mismo_puntaje = [ordenados[i]]
            j = i + 1

            while j < len(ordenados) and float(getattr(ordenados[j], "puntaje", getattr(ordenados[j], "puntaje_postulacion", 0) if isinstance(ordenados[j], dict) else 0)) == float(getattr(ordenados[i], "puntaje", getattr(ordenados[i], "puntaje_postulacion", 0) if isinstance(ordenados[i], dict) else 0)):
                mismo_puntaje.append(ordenados[j])
                j += 1

            espacios = len(cupos) - len(asignados)

            if len(mismo_puntaje) <= espacios:
                asignados.extend(mismo_puntaje)
            else:
                seleccionados = self.resolver_empates(mismo_puntaje, espacios)
                asignados.extend(seleccionados)

            i = j

        return _asignar_a_lista(cupos[:len(asignados)], asignados, carrera)

    def resolver_empates(self, empatados, cupos_disponibles):
        return random.sample(empatados, cupos_disponibles)


class LotteryStrategy(AssignmentStrategy):
    """
    Asignación por lotería: selecciona al azar entre postulados el número de cupos disponibles.
    """

    def assign(self, carrera, aspirantes):
        postulados = _postulados_para_carrera(carrera, aspirantes)
        cupos = [c for c in getattr(carrera, "cupos", []) if getattr(c, "estado", "") == "Disponible"]

        n = min(len(cupos), len(postulados))
        if n == 0:
            return []

        seleccion = random.sample(postulados, k=n)
        return _asignar_a_lista(cupos[:n], seleccion, carrera)

    def resolver_empates(self, empatados, cupos_disponibles):
        return random.sample(empatados, cupos_disponibles)


# ------------------------
# SegmentQuotaStrategy (nueva implementación según reglas solicitadas)
# ------------------------
class SegmentQuotaStrategy(AssignmentStrategy):
    """
    Estrategia que:
    - Prioriza por 'prioridad' (1 primero, luego 2) dentro de población general (segmento 1).
    - Reserva entre 5% y 10% del total de cupos para segmento 2 (política de cuotas).
      - El mínimo es 5% (si hay candidatos), el máximo es 10%.
    - Ordena por puntaje dentro de cada grupo.
    """

    def __init__(self):
        super().__init__()

    def _get_segment(self, a):
        try:
            if isinstance(a, dict):
                return str(a.get("segmento") or a.get("grupo") or "").strip()
            return str(getattr(a, "segmento", None) or getattr(a, "grupo", None) or "").strip()
        except Exception:
            return ""

    def _get_priority(self, a):
        try:
            if isinstance(a, dict):
                p = a.get("prioridad")
            else:
                p = getattr(a, "prioridad", None)
            if p is None or str(p).strip() == "":
                return 2
            return int(p)
        except Exception:
            try:
                return int(float(str(p)))
            except Exception:
                return 2

    def _get_score(self, a):
        try:
            if isinstance(a, dict):
                return float(a.get("puntaje_postulacion") or a.get("puntaje") or a.get("puntaje_post") or 0)
            return float(getattr(a, "puntaje", 0))
        except Exception:
            try:
                return float(str(getattr(a, "puntaje", 0)))
            except Exception:
                return 0.0

    def assign(self, carrera, aspirantes):
        cupos = [c for c in getattr(carrera, "cupos", []) if getattr(c, "estado", "") == "Disponible"]
        total_slots = len(cupos)
        if total_slots == 0:
            return []

        postulados = _postulados_para_carrera(carrera, aspirantes)

        quota_candidates = []
        general_candidates = []
        for a in postulados:
            seg = self._get_segment(a)
            if seg == "2":
                quota_candidates.append(a)
            else:
                general_candidates.append(a)

        quota_candidates = sorted(quota_candidates, key=lambda x: self._get_score(x), reverse=True)

        general_p1 = [a for a in general_candidates if self._get_priority(a) == 1]
        general_p2 = [a for a in general_candidates if self._get_priority(a) != 1]

        general_p1 = sorted(general_p1, key=lambda x: self._get_score(x), reverse=True)
        general_p2 = sorted(general_p2, key=lambda x: self._get_score(x), reverse=True)

        quota_max = int(math.floor(total_slots * 0.10))
        quota_min = int(math.ceil(total_slots * 0.05))

        if len(quota_candidates) == 0:
            quota_min = 0

        # política conservadora: no reservar más que quota_max
        if quota_min > quota_max:
            quota_min = quota_max

        reserved_quota = min(len(quota_candidates), quota_min)
        assigned = []
        idx = 0

        def assign_list(app_list):
            nonlocal idx, assigned
            if idx >= len(cupos) or not app_list:
                return
            take = min(len(app_list), len(cupos) - idx)
            if take <= 0:
                return
            sel = app_list[:take]
            asignados_locales = _asignar_a_lista(cupos[idx:idx+take], sel, carrera)
            assigned.extend(asignados_locales)
            idx += take

        # 1) Asignar a población general prioridad 1
        assign_list(general_p1)

        # 2) Asignar a población general prioridad 2
        assign_list(general_p2)

        # 3) Asignar reserved_quota de quota_candidates
        remaining_cups = len(cupos) - idx
        to_assign_reserved = min(reserved_quota, remaining_cups)
        if to_assign_reserved > 0:
            assign_list(quota_candidates[:to_assign_reserved])
            quota_candidates = quota_candidates[to_assign_reserved:]

        # 4) Permitir asignar cuota extra hasta quota_max
        quota_assigned_count = 0
        try:
            for a in assigned:
                seg = self._get_segment(a)
                if seg == "2":
                    quota_assigned_count += 1
        except Exception:
            quota_assigned_count = 0

        remaining_cups = len(cupos) - idx
        extra_quota_allowed = max(0, quota_max - quota_assigned_count)
        extra_to_assign = min(extra_quota_allowed, remaining_cups, len(quota_candidates))
        if extra_to_assign > 0:
            assign_list(quota_candidates[:extra_to_assign])
            quota_candidates = quota_candidates[extra_to_assign:]

        return assigned


# ------------------------
# Clase wrapper que usa la estrategia
# ------------------------
class Asignacion_cupo:
    """
    Clase contenedora que recibe (carrera, aspirantes, estrategia) y ejecuta la asignación.
    Uso:
      contexto = Asignacion_cupo(carrera, aspirantes, SegmentQuotaStrategy())
      asignados = contexto.asignar_cupos()
    """

    def __init__(self, carrera, aspirantes, strategy: AssignmentStrategy):
        self.carrera = carrera
        self.aspirantes = aspirantes
        self.strategy = strategy
        self.asignados = []

    def asignar_cupos(self):
        try:
            self.asignados = self.strategy.assign(self.carrera, self.aspirantes) or []
        except Exception:
            self.asignados = []
        return self.asignados