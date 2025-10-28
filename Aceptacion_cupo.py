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

#Ejemplo de caso de uso
if __name__ == "__main__":

    # Clases auxiliares simuladas
    class Cupo:
        def __init__(self, id_cupo, carrera, estado="Asignado"):
            self.id_cupo = id_cupo
            self.carrera = carrera
            self.estado = estado

        def aceptar(self):
            self.estado = "Aceptado"
            print(f" Cupo de {self.carrera} ha sido aceptado oficialmente.")

    class Aspirante:
        def __init__(self, nombre, estado="Asignado"):
            self.nombre = nombre
            self.estado = estado

    
    cupo1 = Cupo(1, "Ingeniería en Software")
    aspirante1 = Aspirante("José Herrera")

    
    proceso = Aceptacion_cupo(aspirante1, cupo1)

    
    print(" Intentando aceptar cupo...")
    proceso.aceptar()

    print("\n Generando certificado...")
    proceso.generar_certificado()