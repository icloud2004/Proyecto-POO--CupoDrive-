"""
Módulo de asignación de cupos — versión conectada y robusta.

Exporta:
- Asignacion_cupo: wrapper con método asignar_cupos()
- MultiSegmentStrategy: estrategia que implementa la lógica por segmentos y prioridades.

Diseñado para ser tolerante a aspirantes representados como dicts u objetos,
y a carreras que tengan o no la propiedad .segmentos.
"""

from abc import ABC, abstractmethod
from typing import List
import random


# Estrategia base para asignación de cupos
class AssignmentStrategy(ABC):
    @abstractmethod
    def assign(self, carrera, aspirantes):
        """
        Método que implementa la estrategia de asignación.
        """
        raise NotImplementedError()


# Estrategia multi-segmentos (robusta)
class MultiSegmentStrategy(AssignmentStrategy):
    """
    La estrategia asigna cupos según:
    - Prioridad de los aspirantes.
    - Segmentos y porcentajes.
    - Respeto a los cupos disponibles.
    """

    def __init__(self, tie_breaker: str = "stable", random_seed: int = 42):
        self.tie_breaker = tie_breaker
        self.random_seed = random_seed
        if tie_breaker == "random":
            random.seed(random_seed)

    def assign(self, carrera, aspirantes: List[dict]):
        """
        Lógica principal de asignación de cupos.
        :param carrera: Objeto de la clase Carrera con cupos y segmentos.
        :param aspirantes: Lista de aspirantes como dict o clases.
        :return: Lista de aspirantes asignados.
        """
        # Obtener los cupos disponibles en la carrera
        cupos_disponibles = carrera.obtener_cupos_disponibles()

        # Validar si hay cupos disponibles
        if not cupos_disponibles:
            return []

        # Obtener los segmentos definidos y calcular su distribución inicial
        segmentos = carrera.obtener_segmentos_ordenados()
        total_cupos = len(cupos_disponibles)
        cupos_por_segmento = carrera.distribuir_cupos_por_segmento()

        # Ordenar aspirantes por prioridad (1 primero, luego 2) y desempate por puntaje
        aspirantes_ordenados = sorted(
            aspirantes,
            key=lambda a: (a["prioridad"], -a["puntaje"])
        )

        # Asignar cupos por segmentos
        asignados = []
        for segmento in segmentos:
            nombre_segmento = segmento.nombre
            cantidad_de_cupos = cupos_por_segmento.get(nombre_segmento, 0)

            # Filtrar aspirantes que pertenezcan al segmento
            aspirantes_segmento = [
                a for a in aspirantes_ordenados if a["segmento"] == nombre_segmento
            ][:cantidad_de_cupos]

            # Asignar estos aspirantes a los cupos disponibles
            for cupo, aspirante in zip(cupos_disponibles[:cantidad_de_cupos], aspirantes_segmento):
                cupo.estado = "Asignado"
                cupo.aspirante = aspirante
                aspirante["estado"] = "Asignado"
                aspirante["carrera_asignada"] = carrera.nombre
                asignados.append(aspirante)

            # Reducir los cupos disponibles
            cupos_disponibles = cupos_disponibles[cantidad_de_cupos:]

        # Devolver lista de asignados
        return asignados


# Wrapper que el sistema espera usar para asignar cupos
class Asignacion_cupo:
    """
    Wrapper:
    - Maneja la asignación utilizando la estrategia definida.
    - Recibe `carrera`, `aspirantes` y una `estrategia` (clase o instancia).
    """

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
        """
        Ejecuta la asignación de cupos utilizando la estrategia definida.
        :return: Lista de aspirantes asignados.
        """
        if self.strategy is None:
            return []

        if hasattr(self.strategy, "assign"):
            return self.strategy.assign(self.carrera, self.aspirantes)

        return []


# Public API
__all__ = ["AssignmentStrategy", "MultiSegmentStrategy", "Asignacion_cupo"]