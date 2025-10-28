import csv
from Aspirante import Aspirante

class Cargar_datos:
    def __init__(self, ruta_csv="BaseDatos.csv"):
        self.ruta_csv = ruta_csv
        self.aspirantes = []


    def cargar(self):
        """Carga los aspirantes desde el archivo CSV (BaseDatos.csv)."""
        try:
            with open(self.ruta_csv, newline="", encoding="utf-8") as data:
                lector = csv.reader(data, delimiter=";")
                next(lector)  # Saltar encabezado

                for fila in lector:
                    (
                        ies_id, ies_nombre, identificacion, nombres, apellidos,
                        puntaje_postulacion, prioridad, segmento, nombre_carrera,
                        campus, tipo_cupo, modalidad, nivel, jornada,
                        acepta_estado, fecha_acepta_cupo
                    ) = fila

                  
                    aspirante = Aspirante(
                        cedula=identificacion,
                        nombre=f"{nombres} {apellidos}",
                        puntaje=float(puntaje_postulacion),
                        grupo=segmento,
                        titulos="Bachiller",
                        estado="Postulado",
                        vulnerabilidad="Alta" if int(segmento) == 1 else "Media",
                        fecha_inscripcion="2025-01-10"
                    )
                    self.aspirantes.append(aspirante)

            print(f" Cargados {len(self.aspirantes)} aspirantes desde '{self.ruta_csv}'.")
            return self.aspirantes

        except FileNotFoundError:
            print(f" Error: no se encontró el archivo {self.ruta_csv}.")
            return []
#ejemplo de uso

#instanciamos la clase cargar datos
instancia = Cargar_datos()

#ejecutamos el método cargar
a = instancia.cargar()
for i in a:
    print(f"{i.cedula} {i.nombre} {i.puntaje} {i.grupo} {i.titulos} {i.estado} {i.vulnerabilidad} {i.fecha_inscripcion} \n ")