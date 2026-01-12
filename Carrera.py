from Cupo import Cupo
from Segmento import Segmento

class Carrera:
    def __init__(self, id_carrera, nombre, oferta_cupos, segmentos=None):
        self.id_carrera = id_carrera
        self.nombre = nombre
        self.oferta_cupos = int(oferta_cupos)   # cupos disponibles
        self.segmentos = segmentos if segmentos else []  # Lista de objetos Segmento
        self.cupos = []     # Lista de objetos Cupo generados

        # Inicializamos los cupos disponibles
        for i in range(1, self.oferta_cupos + 1):
            self.cupos.append(Cupo(id_cupo=f"{id_carrera}-{i}", carrera=self.nombre))

    def agregar_segmento(self, segmento):
        """Agrega un segmento (grupo) asociado a la carrera."""
        self.segmentos.append(segmento)
        print(f" Segmento '{segmento.nombre}' agregado a la carrera {self.nombre}")

    def obtener_cupos_disponibles(self):
        """Devuelve una lista de cupos que están disponibles."""
        return [c for c in self.cupos if c.estado == "Disponible"]

    def mostrar_informacion(self):
        """Imprime información general de la carrera y sus cupos."""
        disponibles = len(self.obtener_cupos_disponibles())
        print(f"\nCARRERA: {self.nombre}")
        print(f"Oferta total: {self.oferta_cupos} cupos")
        print(f"Cupos disponibles: {disponibles}")
        print("Segmentos:")
        for seg in self.segmentos:
            print(f" - {seg.nombre} ({seg.porcentaje}%)")

    def actualizar_oferta(self, nueva_oferta):
        """
        Actualiza la oferta de cupos para la carrera.
        - Si nueva_oferta > oferta actual: añade cupos nuevos al final.
        - Si nueva_oferta < oferta actual: elimina cupos disponibles al final.
          No permite reducir por debajo del número de cupos ya asignados.
        Lanza ValueError si la operación no es posible.
        """
        try:
            nueva = int(nueva_oferta)
        except Exception:
            raise ValueError("La nueva oferta debe ser un número entero.")

        if nueva < 0:
            raise ValueError("La nueva oferta debe ser >= 0.")

        actuales = len(self.cupos)
        asignados = len([c for c in self.cupos if getattr(c, "estado", "") not in ("Disponible", "") and getattr(c, "estado", "") != "Disponible"])
        # para compatibilidad: también contar estados distintos de "Disponible"
        asignados = len([c for c in self.cupos if getattr(c, "estado", "") != "Disponible"])

        if nueva < asignados:
            # no podemos reducir por debajo de los asignados
            raise ValueError(f"No se puede reducir la oferta a {nueva}: hay {asignados} cupos ya asignados.")

        if nueva == actuales:
            # nada que hacer
            self.oferta_cupos = nueva
            return

        if nueva > actuales:
            # Añadir nuevos cupos
            start = actuales + 1
            for i in range(start, nueva + 1):
                # id único siguiendo el patrón id_carrera-i
                new_id = f"{self.id_carrera}-{i}"
                self.cupos.append(Cupo(id_cupo=new_id, carrera=self.nombre))
            self.oferta_cupos = nueva
            print(f"Se añadieron {nueva - actuales} cupos a la carrera {self.nombre}.")
            return

        if nueva < actuales:
            # Remover cupos disponibles desde el final
            # Buscamos cupos eliminables (estado "Disponible")
            eliminables = [c for c in reversed(self.cupos) if getattr(c, "estado", "") == "Disponible"]
            cantidad_a_quitar = actuales - nueva
            if len(eliminables) < cantidad_a_quitar:
                # Si no hay suficientes cupos disponibles al final, buscamos disponibles en toda la lista
                disponibles = [c for c in self.cupos if getattr(c, "estado", "") == "Disponible"]
                if len(disponibles) < cantidad_a_quitar:
                    raise ValueError("No hay suficientes cupos disponibles para reducir la oferta (algunos están asignados).")
                # eliminamos de la lista de disponibles (últimos)
                to_remove = disponibles[-cantidad_a_quitar:]
            else:
                to_remove = eliminables[:cantidad_a_quitar]

            # Eliminar los cupos seleccionados de self.cupos
            for rem in to_remove:
                try:
                    self.cupos.remove(rem)
                except ValueError:
                    pass
            self.oferta_cupos = nueva
            print(f"Se eliminaron {cantidad_a_quitar} cupos de la carrera {self.nombre}.")
            return

#ejemplo de uso
if __name__ == "__main__":
    #creamos instancias de segmentos
    politica_cuota = Segmento("politica de cuota", 10, "Discriminados por las IES públicas")
    vulnerabilidad_socioeconomica = Segmento("Vulnerabilidad socioeconomica", 30, "pobreza")
    merito_academico = Segmento("Mérito académic", 30, "cuadro de honor de los Colegios")
    bachilleres = Segmento("segmento", 30, "Discriminados por las IES públicas")

    #instanciamos la carrera de software con sus atributos
    carrera_software = Carrera("1", "Software", 5, [politica_cuota,vulnerabilidad_socioeconomica, merito_academico, bachilleres] )

    carrera_software.mostrar_informacion()
    print("Reduciendo oferta a 3")
    carrera_software.actualizar_oferta(3)
    carrera_software.mostrar_informacion()
    print("Aumentando oferta a 7")
    carrera_software.actualizar_oferta(7)
    carrera_software.mostrar_informacion()