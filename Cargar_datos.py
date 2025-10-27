import csv
from Aspirante import Aspirante

class Cargar_datos:
    def __init__(self, ruta_csv="BaseDatos.csv"):
        self.ruta_csv = ruta_csv
        self.aspirantes = []
    def cargar(self):
        with open(self.ruta_csv, newline="", encoding="utf-8") as data:
            lector = csv.reader(data, delimiter=";")
            next(lector)  # saltar encabezado

            for fila in lector:
                (
                    ies_id, ies_nombre, identificacion, nombres, apellidos,
                    puntaje_postulacion, prioridad, segmento, nombre_carrera,
                    campus, tipo_cupo, modalidad, nivel, jornada,
                    acepta_estado, fecha_acepta_cupo
                ) = fila

                aspirante = Aspirante(
                    identificacion=identificacion,
                    nombres=nombres,
                    apellidos=apellidos,
                    puntaje=puntaje_postulacion,
                    carrera=nombre_carrera
                )
                self.aspirantes.append(aspirante)

        print(f" Cargados {len(self.aspirantes)} aspirantes desde {self.ruta_csv}.")
        return self.aspirantes
