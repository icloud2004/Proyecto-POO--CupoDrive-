from Persona import Persona

class Aspirante(Persona):
    def __init__(self, cedula, nombre, puntaje, grupo, titulos, estado, vulnerabilidad, fecha_inscripcion):
        super().__init__(cedula, nombre)
        self.puntaje = puntaje
        self.grupo = grupo
        self.titulos = titulos
        self.estado = estado
        self.vulnerabilidad = vulnerabilidad
        self.fecha_inscripcion = fecha_inscripcion

    def rechazar_cupo(self, cupo):
        pass

    def aceptar_cupo(self, cupo):
        pass

    def descripcion(self):
        return f"Aspirante: {self.nombre}"