from typing import List, Dict, Tuple, Optional
from Cupo import Cupo
from Segmento import Segmento
import math

class Carrera:
    def __init__(self, id_carrera: str, nombre: str, oferta_cupos: int,
                 segmentos: Optional[List[Segmento]] = None, campus: Optional[str] = None,
                 generar_cupos: bool = True):
        """
        Modelo de carrera.
        - generar_cupos: si es True (por defecto) intenta crear objetos Cupo según oferta_cupos
          solo si no existen cupos previamente (evita regenerar sobre persistencia).
        """
        self.id_carrera = id_carrera
        self.nombre = nombre
        try:
            self.oferta_cupos = int(oferta_cupos)
        except Exception:
            self.oferta_cupos = 0
        self.segmentos: List[Segmento] = list(segmentos) if segmentos else []
        self.campus = campus
        # cupos: lista de objetos Cupo (o estructuras compatibles)
        self.cupos: List = []

        # Generar cupos solo si se solicita y no hay ya cupos (permite reconstrucción desde persistencia)
        if generar_cupos and not getattr(self, "cupos", None):
            for i in range(1, max(0, self.oferta_cupos) + 1):
                try:
                    self.cupos.append(Cupo(id_cupo=f"{self.id_carrera}-{i}", carrera=self.nombre))
                except Exception:
                    # fallback: objeto simple con atributos mínimos
                    cup = type("SimpleCupo", (), {})()
                    setattr(cup, "id_cupo", f"{self.id_carrera}-{i}")
                    setattr(cup, "carrera", self.nombre)
                    setattr(cup, "estado", "Disponible")
                    setattr(cup, "aspirante", None)
                    self.cupos.append(cup)

    # ----------------
    # Métodos de segmentos
    # ----------------
    def get_segmentos_dict(self) -> List[Dict]:
        """Devuelve la lista de segmentos como dicts ordenados por 'orden'."""
        return [s.to_dict() for s in sorted(self.segmentos, key=lambda x: x.orden)]

    def agregar_segmento(self, segmento: Segmento) -> None:
        """
        Agrega un segmento. Si ya existe uno con el mismo nombre (case-insensitive)
        lo reemplaza.
        """
        for i, s in enumerate(self.segmentos):
            if s.nombre.strip().lower() == segmento.nombre.strip().lower():
                self.segmentos[i] = segmento
                return
        self.segmentos.append(segmento)

    def actualizar_segmento(self, nombre_segmento: str,
                            porcentaje: Optional[float] = None,
                            orden: Optional[int] = None,
                            min_pct: Optional[float] = None,
                            max_pct: Optional[float] = None,
                            descripcion: Optional[str] = None) -> bool:
        """
        Actualiza propiedades de un segmento por nombre. Devuelve True si lo actualizó.
        """
        for seg in self.segmentos:
            if seg.nombre.strip().lower() == nombre_segmento.strip().lower():
                if porcentaje is not None:
                    seg.porcentaje = float(porcentaje)
                if orden is not None:
                    seg.orden = int(orden)
                if min_pct is not None:
                    seg.min_pct = float(min_pct)
                if max_pct is not None:
                    seg.max_pct = float(max_pct)
                if descripcion is not None:
                    seg.descripcion = descripcion
                return True
        return False

    def eliminar_segmento(self, nombre_segmento: str) -> bool:
        """Elimina un segmento por nombre. Devuelve True si lo eliminó."""
        for seg in list(self.segmentos):
            if seg.nombre.strip().lower() == nombre_segmento.strip().lower():
                self.segmentos.remove(seg)
                return True
        return False

    def validar_sumatorio_segmentos(self) -> Tuple[bool, float]:
        """
        Valida que la suma de porcentajes de los segmentos sea aproximadamente 100.
        Devuelve (es_valido, suma_actual).
        """
        suma = sum([float(seg.porcentaje or 0.0) for seg in self.segmentos])
        return (abs(suma - 100.0) < 0.0001, suma)

    def obtener_segmentos_ordenados(self) -> List[Segmento]:
        """Devuelve lista de Segmento ordenados por campo 'orden' ascendente."""
        return sorted(self.segmentos, key=lambda s: int(getattr(s, "orden", 100)))

    # ----------------
    # Distribución simple por segmentos (helper)
    # ----------------
    def distribuir_cupos_por_segmento(self) -> Dict[str, int]:
        """
        Calcula una distribución inicial de cupos por segmento usando floor/round y
        reparte sobrantes a 'Población general' si existe o al último segmento.
        Retorna dict {segmento_nombre: cupos}.
        Nota: Esta función sólo calcula una propuesta; la asignación real la hace la estrategia.
        """
        oferta = max(0, int(self.oferta_cupos))
        asignados: Dict[str, int] = {}
        total_asignado = 0

        segmentos = self.obtener_segmentos_ordenados()
        if not segmentos:
            return {"Población general": oferta}

        # Calcular cupos por segmento (round para aproximar)
        for seg in segmentos:
            n = int(round(oferta * (float(seg.porcentaje or 0.0) / 100.0)))
            asignados[seg.nombre] = n
            total_asignado += n

        # Ajustar diferencia por redondeo
        diff = oferta - total_asignado
        if diff != 0:
            # Preferir Población general si existe
            idx_pop = None
            for i, s in enumerate(segmentos):
                if s.nombre.strip().lower().startswith("pobl"):
                    idx_pop = i
                    break
            if idx_pop is None:
                # ajustar último segmento
                last = segmentos[-1].nombre
                asignados[last] = asignados.get(last, 0) + diff
            else:
                asignados[segmentos[idx_pop].nombre] = asignados.get(segmentos[idx_pop].nombre, 0) + diff

        return asignados

    # ----------------
    # Cupos helpers / gestión oferta
    # ----------------
    def obtener_cupos_disponibles(self) -> List:
        """Devuelve una lista de cupos que están disponibles (estado == 'Disponible')."""
        return [c for c in getattr(self, "cupos", []) if getattr(c, "estado", "") == "Disponible"]

    def mostrar_informacion(self) -> None:
        """Imprime información general de la carrera y sus cupos/segmentos."""
        disponibles = len(self.obtener_cupos_disponibles())
        print(f"\nCARRERA: {self.nombre} (campus: {self.campus})")
        print(f"Oferta total: {self.oferta_cupos} cupos")
        print(f"Cupos disponibles: {disponibles}")
        print("Segmentos:")
        for seg in self.obtener_segmentos_ordenados():
            print(f" - {seg.nombre} : {seg.porcentaje}% (orden {seg.orden})")

    def actualizar_oferta(self, nueva_oferta: int) -> None:
        """
        Actualiza la oferta de cupos para la carrera.
        - Si nueva_oferta > oferta actual: añade cupos nuevos al final.
        - Si nueva_oferta < oferta actual: elimina cupos disponibles (no asignados) desde el final.
        Lanza ValueError si la operación no es posible (ej. reducir por debajo de asignados).
        """
        try:
            nueva = int(nueva_oferta)
        except Exception:
            raise ValueError("La nueva oferta debe ser un número entero.")

        if nueva < 0:
            raise ValueError("La nueva oferta debe ser >= 0.")

        actuales = len(getattr(self, "cupos", []))
        asignados = len([c for c in self.cupos if getattr(c, "estado", "") != "Disponible"])

        if nueva < asignados:
            raise ValueError(f"No se puede reducir la oferta a {nueva}: hay {asignados} cupos ya asignados.")

        if nueva == actuales:
            self.oferta_cupos = nueva
            return

        if nueva > actuales:
            start = actuales + 1
            for i in range(start, nueva + 1):
                try:
                    self.cupos.append(Cupo(id_cupo=f"{self.id_carrera}-{i}", carrera=self.nombre))
                except Exception:
                    cup = type("SimpleCupo", (), {})()
                    setattr(cup, "id_cupo", f"{self.id_carrera}-{i}")
                    setattr(cup, "carrera", self.nombre)
                    setattr(cup, "estado", "Disponible")
                    setattr(cup, "aspirante", None)
                    self.cupos.append(cup)
            self.oferta_cupos = nueva
            return

        # nueva < actuales: remover cupos disponibles desde el final
        eliminables = [c for c in reversed(self.cupos) if getattr(c, "estado", "") == "Disponible"]
        cantidad_a_quitar = actuales - nueva
        if len(eliminables) < cantidad_a_quitar:
            disponibles = [c for c in self.cupos if getattr(c, "estado", "") == "Disponible"]
            if len(disponibles) < cantidad_a_quitar:
                raise ValueError("No hay suficientes cupos disponibles para reducir la oferta (algunos están asignados).")
            to_remove = disponibles[-cantidad_a_quitar:]
        else:
            to_remove = eliminables[:cantidad_a_quitar]

        for rem in to_remove:
            try:
                self.cupos.remove(rem)
            except ValueError:
                pass

        self.oferta_cupos = nueva