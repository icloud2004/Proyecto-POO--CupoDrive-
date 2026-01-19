#PATRON DE DISEÑO: DECORATOR
from abc import ABC, abstractmethod
from datetime import datetime
# INTERFAZ
class ProcesoAceptacion(ABC):
    @abstractmethod
    def aceptar(self):
        pass
# CLASE CONCRETA
class AceptacionCupo(ProcesoAceptacion):

    def __init__(self, aspirante, cupo):
        self.aspirante = aspirante
        self.cupo = cupo
        self.fecha_aceptacion = None
    def aceptar(self):
        if self.cupo.estado == "Asignado" and self.aspirante.estado == "Asignado":
            self.cupo.aceptar()
            self.aspirante.estado = "Aceptado"
            self.fecha_aceptacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Cupo aceptado el {self.fecha_aceptacion}")
        else:
            print("No se puede aceptar el cupo")
# DECORATOR BASE
class AceptacionDecorator(ProcesoAceptacion):
    def __init__(self, proceso: ProcesoAceptacion):
        self._proceso = proceso
    def aceptar(self):
        self._proceso.aceptar()
    def __getattr__(self, name):
        return getattr(self._proceso, name)
# DECORATOR CONCRETO 1
# Generación de Certificado
class CertificadoAceptacionDecorator(AceptacionDecorator):
    def aceptar(self):
        super().aceptar()
        aspirante = self._proceso.aspirante
        if aspirante.estado == "Aceptado":
            print("\n--- CERTIFICADO DE ACEPTACIÓN ---")
            print(f"Aspirante: {aspirante.nombre}")
            print(f"Carrera: {self._proceso.cupo.carrera}")
            print(f"Fecha: {self._proceso.fecha_aceptacion}")
# DECORATOR CONCRETO 2
# Registro en sistema
class RegistroAceptacionDecorator(AceptacionDecorator):
    def aceptar(self):
        super().aceptar()
        if self._proceso.aspirante.estado == "Aceptado":
            print("Registro guardado en el sistema académico.")
# CLASES AUXILIARES
class Cupo:
    def __init__(self, id_cupo, carrera, estado="Asignado"):
        self.id_cupo = id_cupo
        self.carrera = carrera
        self.estado = estado
    def aceptar(self):
        self.estado = "Aceptado"
        print(f"Cupo de {self.carrera} aceptado.")
class Aspirante:
    def __init__(self, nombre, estado="Asignado"):
        self.nombre = nombre
        self.estado = estado
# EJEMPLO DE USO
if __name__ == "__main__":
    cupo = Cupo(1, "Ingeniería en Software")
    aspirante = Aspirante("José Herrera")
    proceso_base = AceptacionCupo(aspirante, cupo)
    proceso_con_registro = RegistroAceptacionDecorator(proceso_base)
    proceso_completo = CertificadoAceptacionDecorator(proceso_con_registro)
    proceso_completo.aceptar()