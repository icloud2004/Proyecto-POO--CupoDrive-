from datetime import datetime

class Aceptacion_cupo:

    def __init__(self, aspirante, cupo):
        self.aspirante = aspirante  # Inyección de dependencia
        self.cupo = cupo            # Inyección de dependencia
        self.fecha_aceptacion = None

    def aceptar(self):
        if self.cupo.estado == "Asignado" and self.aspirante.estado == "Asignado":
            self.cupo.aceptar()
            self.aspirante.estado = "Aceptado"
            self.fecha_aceptacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f" Cupo aceptado el {self.fecha_aceptacion}")
        else:
            print(f" No se puede aceptar el cupo: {self.aspirante.nombre} no tiene un cupo asignado válido.")

    def generar_certificado(self):
        if self.aspirante.estado == "Aceptado":
            print(f"\n CERTIFICADO DE ACEPTACIÓN DE CUPO")
            print(f"Aspirante: {self.aspirante.nombre}")
            print(f"Carrera: {self.cupo.carrera}")
            print(f"Fecha de aceptación: {self.fecha_aceptacion}")
        else:
            print(" No se puede generar certificado, el aspirante no ha aceptado un cupo.")