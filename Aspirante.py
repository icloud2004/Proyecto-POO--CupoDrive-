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
