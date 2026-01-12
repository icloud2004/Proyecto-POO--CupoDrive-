from Cupo import Cupo
from Segmento import Segmento
from typing import List, Dict
import math

class Carrera:
    def __init__(self, id_carrera, nombre, oferta_cupos, segmentos: List[Segmento]=None, campus=None):
        self.id_carrera = id_carrera
        self.nombre = nombre
        self.oferta_cupos = int(oferta_cupos)
        self.segmentos = segmentos if segmentos else []  # Lista de Segmento
        self.campus = campus
        self.cupos = []
        for i in range(1, self.oferta_cupos + 1):
            self.cupos.append(Cupo(id_cupo=f"{id_carrera}-{i}", carrera=self.nombre))

    # Segmentos management
    def agregar_segmento(self, segmento: Segmento):
        self.segmentos.append(segmento)
        print(f" Segmento '{segmento.nombre}' agregado a la carrera {self.nombre}")

    def actualizar_segmento(self, nombre_segmento: str, porcentaje: float, min_pct: float = None, max_pct: float = None):
        for seg in self.segmentos:
            if seg.nombre.strip().lower() == nombre_segmento.strip().lower():
                seg.porcentaje = float(porcentaje)
                if min_pct is not None:
                    seg.min_pct = float(min_pct)
                if max_pct is not None:
                    seg.max_pct = float(max_pct)
                return True
        return False

    def eliminar_segmento(self, nombre_segmento: str):
        for seg in list(self.segmentos):
            if seg.nombre.strip().lower() == nombre_segmento.strip().lower():
                self.segmentos.remove(seg)
                return True
        return False

    def validar_porcentajes(self) -> (bool, float):
        """
        Valida la suma de porcentajes.
        Devuelve (es_valido, suma_actual)
        """
        suma = sum([float(seg.porcentaje or 0.0) for seg in self.segmentos])
        return (suma <= 100.0, suma)

    def distribuir_cupos_por_segmento(self) -> Dict[str, int]:
        """
        Calcula cuántos cupos corresponden a cada segmento.
        Rellena automáticamente la diferencia pendiente en 'Población general'.
        Retorna dict {segmento_nombre: cupos}
        """
        oferta = self.oferta_cupos
        asignados = {}
        total_asignado = 0

        # Primero calcular cupos por segmento (floor)
        for seg in self.segmentos:
            n = seg.calcular_cupos_total(oferta)
            asignados[seg.nombre] = n
            total_asignado += n

        # Si existe segmento población general entre segmentos, lo usamos; si no, lo creamos con 0%
        pobl_general_name = None
        for seg in self.segmentos:
            if seg.nombre.strip().lower() in ["población general", "poblacion general", "poblacion general"]:
                pobl_general_name = seg.nombre
                break

        # sobrante
        sobrante = oferta - total_asignado
        if sobrante > 0:
            if pobl_general_name:
                asignados[pobl_general_name] = asignados.get(pobl_general_name, 0) + sobrante
            else:
                # añadir virtualmente
                asignados["Población general"] = asignados.get("Población general", 0) + sobrante

        # si hubo sobreasignación (por redondeos) recortar de poblacion general preferentemente
        if sum(asignados.values()) > oferta:
            exceso = sum(asignados.values()) - oferta
            if pobl_general_name and asignados.get(pobl_general_name, 0) >= exceso:
                asignados[pobl_general_name] -= exceso
            else:
                # recortar desde cualquier segmento sin bajar de su min_pct (simplificado)
                for seg in self.segmentos:
                    nombre = seg.nombre
                    reducible = max(0, asignados.get(nombre, 0) - int((seg.min_pct/100.0)*oferta))
                    take = min(reducible, exceso)
                    asignados[nombre] -= take
                    exceso -= take
                    if exceso <= 0:
                        break

        return asignados

    # resto de métodos existentes (obtener_cupos_disponibles, mostrar_informacion, actualizar_oferta...) se mantienen
    def obtener_cupos_disponibles(self):
        return [c for c in self.cupos if getattr(c, "estado", "") == "Disponible"]

    def mostrar_informacion(self):
        disponibles = len(self.obtener_cupos_disponibles())
        print(f"\nCARRERA: {self.nombre} (campus: {self.campus})")
        print(f"Oferta total: {self.oferta_cupos} cupos")
        print(f"Cupos disponibles: {disponibles}")
        print("Segmentos:")
        for seg in self.segmentos:
            print(f" - {seg.nombre} ({seg.porcentaje}%)")
