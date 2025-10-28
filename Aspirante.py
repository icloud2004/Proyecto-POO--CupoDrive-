from Persona import Persona

class Aspirante(Persona):
 
    def __init__(self, cedula, nombre, puntaje, grupo, titulos, estado, vulnerabilidad, fecha_inscripcion):
        super().__init__(cedula, nombre)
        self.puntaje = float(puntaje)
        self.grupo = grupo
        self.titulos = titulos
        self.estado = estado  # Puede ser "Postulado", "Aceptado" o "Rechazado"
        self.vulnerabilidad = vulnerabilidad  
        self.fecha_inscripcion = fecha_inscripcion
        self.carrera_asignada = None  # Se llena al asignar cupo

    def aceptar_cupo(self, cupo):
        self.estado = "Aceptado"
        self.carrera_asignada = cupo.carrera
        print(f" {self.nombre} ha aceptado el cupo en {cupo.carrera}.")

    def rechazar_cupo(self, cupo):
        self.estado = "Rechazado"
        self.carrera_asignada = None
        print(f" {self.nombre} ha rechazado el cupo en {cupo.carrera}.")

    def descripcion(self):
        return f"Aspirante: {self.nombre} ({self.puntaje} puntos, estado: {self.estado})
        from Persona import Persona

#ejemplos uso

class Cupo:
    def __init__(self, id_cupo, carrera):
        self.id_cupo = id_cupo
        self.carrera = carrera

if __name__ == "__main__":
    aspirante1 = Aspirante(
        cedula="1100456789",
        nombre="José Herrera",
        puntaje=812,
        grupo="Mérito Académico",
        titulos="Bachiller en Ciencias",
        estado="Postulado",
        vulnerabilidad="Media",
        fecha_inscripcion="2025-02-01"
    )

    aspirante2 = Aspirante(
        cedula="1100567890",
        nombre="María López",
        puntaje=720,
        grupo="Población General",
        titulos="Bachiller Técnico",
        estado="Postulado",
        vulnerabilidad="Alta",
        fecha_inscripcion="2025-02-02"
    )

    
    cupo_software = Cupo(id_cupo=1, carrera="Ingeniería en Software")
    cupo_ti = Cupo(id_cupo=2, carrera="Tecnologías de la Información")

    print(" Estado inicial:")
    print(aspirante1.descripcion())
    print(aspirante2.descripcion())
    print()

    aspirante1.aceptar_cupo(cupo_software)
    aspirante2.rechazar_cupo(cupo_ti)
    print()

    print(" Estado final:")
    print(aspirante1.descripcion())
    print(aspirante2.descripcion())
