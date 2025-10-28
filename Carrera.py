from Cupo import Cupo
from Segmento import Segmento

class Carrera:
    def __init__(self, id_carrera, nombre, oferta_cupos, segmentos=None):
        self.id_carrera = id_carrera
        self.nombre = nombre
        self.oferta_cupos = oferta_cupos   # cupos disponibles
        self.segmentos = segmentos if segmentos else []  # Lista de objetos Segmento
        self.cupos = []     # Lista de objetos Cupo generados

        # Inicializamos los cupos disponibles
        for i in range(1, oferta_cupos + 1):
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
            
#ejemplo de uso

#creamos instancias de segmentos
politica_cuota = Segmento("politica de cuota", 10, "Discriminados por las IES públicas")
vulnerabilidad_socioeconomica = Segmento("Vulnerabilidad socioeconómica", 30, "pobreza")
merito_academico = Segmento("Mérito acádemico", 30, "cuadro de honor de los Colegios")
bachilleres = Segmento("segmento", 30, "Discriminados por las IES públicas")


#instanciamos la carrera de software con sus atributos
carrera_software = Carrera(1,"Software", 10, [politica_cuota,vulnerabilidad_socioeconomica,
                                              merito_academico, bachilleres] )

#hacemos uso del metodo mostrar info
carrera_software.mostrar_informacion()