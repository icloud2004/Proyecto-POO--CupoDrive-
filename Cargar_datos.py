import csv
from Aspirante import Aspirante

class Cargar_datos:
    # Esta variable guardará la única instancia de la clase
    _instancia_unica = None

    def __init__(self, ruta_csv="BaseDatos.csv"):
        self.ruta_csv = ruta_csv
        self.aspirantes = []
        self.ya_cargo = False # Para saber si ya leímos el archivo

    @classmethod
    def obtener_instancia(cls):
        """Este método asegura que solo se cree un objeto"""
        if cls._instancia_unica is None:
            cls._instancia_unica = cls()
        return cls._instancia_unica

    def cargar(self):
        # Si ya cargamos los datos antes, no los volvemos a leer
        if self.ya_cargo:
            return self.aspirantes

        try:
            with open(self.ruta_csv, newline="", encoding="utf-8") as data:
                lector = csv.reader(data, delimiter=";")
                next(lector)  # Saltamos encabezado

                for fila in lector:
                    (
                        ies_id, ies_nombre, identificacion, nombres, apellidos,
                        puntaje_postulacion, prioridad, segmento, nombre_carrera,
                        campus, tipo_cupo, modalidad, nivel, jornada,
                        acepta_estado, fecha_acepta_cupo
                    ) = fila

                    aspirante = Aspirante(
                        ies_id=ies_id,
                        ies_nombre=ies_nombre,
                        cedula=identificacion,
                        nombre=f"{nombres} {apellidos}",
                        puntaje=float(puntaje_postulacion),
                        prioridad=int(prioridad),
                        carrera=nombre_carrera,
                        campus=campus,
                        tipo_cupo=tipo_cupo,
                        modalidad=modalidad,
                        nivel=nivel,
                        jornada=jornada,
                        acepta_estado=acepta_estado,
                        fecha_acepta_cupo=fecha_acepta_cupo,
                        grupo=segmento,
                        titulos="Bachiller",
                        estado="Postulado",
                        vulnerabilidad="Alta" if int(segmento) == 1 else "Media",
                        fecha_inscripcion="2025-01-10"
                    )
                    self.aspirantes.append(aspirante)

            self.ya_cargo = True # Marcamos que ya terminó
            print(f"Éxito: {len(self.aspirantes)} aspirantes listos.")
            return self.aspirantes

        except FileNotFoundError:
            print("Error: El archivo no existe.")
            return []

# --- Cómo se usa ahora ---
# En lugar de hacer: objeto = Cargar_datos()
# Usamos el método que creamos:
instancia = Cargar_datos.obtener_instancia()
lista_aspirantes = instancia.cargar()