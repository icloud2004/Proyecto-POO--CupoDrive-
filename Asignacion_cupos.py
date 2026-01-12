"""
Asignación de cupos por segmentos según reglamento.
Archivo renombrado desde 'Asignación_cupos.py' a 'Asignacion_cupos.py'.
"""

import random
from collections import defaultdict
from typing import List

# Orden de segmentos según normativa:
SEGMENT_ORDER = [
    "Política de cuotas",
    "Política de cuotas",
    "Grupo de política de cuotas",
    "Grupo de mayor vulnerabilidad socioeconómica",
    "Mayor vulnerabilidad",
    "Vulnerabilidad",
    "Mérito Académico",
    "Mérito",
    "Otros Reconocimientos al Mérito",
    "Bachilleres pueblos",
    "Bachilleres",
    "Población general",
    "Poblacion general",
    "Población General"
]

def _normalizar_nombre(n):
    return str(n or "").strip().lower()

def _segment_priority_index(nombre):
    n = _normalizar_nombre(nombre)
    for idx, s in enumerate(SEGMENT_ORDER):
        if _normalizar_nombre(s) == n:
            return idx
    if "poblacion" in n or "población" in n:
        return len(SEGMENT_ORDER) - 1
    return len(SEGMENT_ORDER)

def _vulnerabilidad_index(asp):
    v = getattr(asp, "vulnerabilidad", "")
    if not v:
        return 99
    v = str(v).strip().lower()
    if v == "alta":
        return 1
    if v == "media":
        return 2
    if v == "baja":
        return 3
    try:
        return int(v)
    except Exception:
        return 99

def _fecha_inscripcion_key(asp):
    return getattr(asp, "fecha_inscripcion", "") or getattr(asp, "fecha_inscripcion_str", "")


def asignar_cupos_por_segmentos(carrera, aspirantes: List):
    """
    Retorna lista de aspirantes asignados (objetos o dicts), y modifica cupos de carrera.cupos.
    Algoritmo:
    1. calcular cupos por segmento (carrera.distribuir_cupos_por_segmento)
    2. construir pools de candidatos: para cada aspirante determinar el segmento en el que participa primero
       (el que más lo favorezca según orden)
    3. por cada segmento en orden, asignar por mérito (puntaje) los cupos disponibles
    4. si quedan cupos sin llenar, reasignar a población general por mérito
    """
    seg_cupos = carrera.distribuir_cupos_por_segmento()
    oferta_total = carrera.oferta_cupos
    candidatos_por_segmento = defaultdict(list)
    restantes = []

    for a in aspirantes:
        segmentos_eligibles = []
        for seg in carrera.segmentos:
            try:
                if seg.verificar_criterios(a):
                    segmentos_eligibles.append(seg)
            except Exception:
                continue

        if not segmentos_eligibles:
            restantes.append(a)
            continue

        segmentos_eligibles_sorted = sorted(segmentos_eligibles, key=lambda s: _segment_priority_index(s.nombre))
        elegido = segmentos_eligibles_sorted[0]
        candidatos_por_segmento[elegido.nombre].append(a)

    poblacion_general_name = None
    for s in carrera.segmentos:
        if _normalizar_nombre(s.nombre).startswith("pobl"):
            poblacion_general_name = s.nombre
            break
    if not poblacion_general_name:
        poblacion_general_name = "Población general"

    candidatos_por_segmento[poblacion_general_name].extend(restantes)

    asignados = []
    cupos_ocupados = 0

    nombres_presentes = set(list(seg_cupos.keys()) + [poblacion_general_name])
    segmentos_a_iterar = []
    for pref in SEGMENT_ORDER:
        for real in nombres_presentes:
            if _normalizar_nombre(pref) == _normalizar_nombre(real) and real not in segmentos_a_iterar:
                segmentos_a_iterar.append(real)
    for real in nombres_presentes:
        if real not in segmentos_a_iterar:
            segmentos_a_iterar.append(real)

    for seg_nombre in segmentos_a_iterar:
        cupos_seg = seg_cupos.get(seg_nombre, 0)
        if cupos_seg <= 0:
            continue
        pool = candidatos_por_segmento.get(seg_nombre, [])
        pool_filtrado = [p for p in pool if p not in asignados]
        def puntaje_key(a):
            if isinstance(a, dict):
                return float(a.get("puntaje_postulacion") or a.get("puntaje") or 0)
            return float(getattr(a, "puntaje", 0) or 0)
        pool_filtrado.sort(key=lambda x: puntaje_key(x), reverse=True)

        selected = []
        i = 0
        while len(selected) < cupos_seg and i < len(pool_filtrado):
            current = pool_filtrado[i]
            current_score = puntaje_key(current)
            tie_group = [current]
            j = i + 1
            while j < len(pool_filtrado) and puntaje_key(pool_filtrado[j]) == current_score:
                tie_group.append(pool_filtrado[j])
                j += 1

            espacios = cupos_seg - len(selected)
            if len(tie_group) <= espacios:
                selected.extend(tie_group)
            else:
                def tie_sort_key(a):
                    vi = _vulnerabilidad_index(a)
                    fecha = _fecha_inscripcion_key(a) or ""
                    return (vi, fecha)
                try:
                    tie_group_sorted = sorted(tie_group, key=tie_sort_key)
                    selected.extend(tie_group_sorted[:espacios])
                except Exception:
                    selected.extend(random.sample(tie_group, espacios))

            i = j

        cupos_disponibles = [c for c in getattr(carrera, "cupos", []) if getattr(c, "estado", "") == "Disponible"]
        n_to_assign = min(len(selected), len(cupos_disponibles))
        for cupo_obj, aspirante in zip(cupos_disponibles[:n_to_assign], selected[:n_to_assign]):
            try:
                cupo_obj.asignar_aspirante(aspirante)
            except Exception:
                try:
                    cupo_obj.aspirante = aspirante
                    cupo_obj.estado = "Asignado"
                except Exception:
                    pass
            asignados.append(aspirante)
            cupos_ocupados += 1

    cupos_libres = [c for c in getattr(carrera, "cupos", []) if getattr(c, "estado", "") == "Disponible"]
    if cupos_libres:
        pool_final = [a for a in aspirantes if a not in asignados]
        def key_pf(x):
            if isinstance(x, dict):
                return float(x.get("puntaje_postulacion") or x.get("puntaje") or 0)
            return float(getattr(x, "puntaje", 0) or 0)
        pool_final.sort(key=lambda x: key_pf(x), reverse=True)
        n = min(len(cupos_libres), len(pool_final))
        for cupo_obj, aspirante in zip(cupos_libres[:n], pool_final[:n]):
            try:
                cupo_obj.asignar_aspirante(aspirante)
            except Exception:
                try:
                    cupo_obj.aspirante = aspirante
                    cupo_obj.estado = "Asignado"
                except Exception:
                    pass
            asignados.append(aspirante)
            cupos_ocupados += 1

    return asignados

# Clase wrapper para compatibilidad con Main.py
class Asignacion_cupo:
    def __init__(self, carrera, aspirantes):
        self.carrera = carrera
        self.aspirantes = aspirantes
        self.asignados = []

    def asignar_cupos(self):
        self.asignados = asignar_cupos_por_segmentos(self.carrera, self.aspirantes)
        return self.asignados
