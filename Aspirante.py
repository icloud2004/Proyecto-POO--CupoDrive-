from Persona import Persona

class Aspirante(Persona):
    def __init__(self, cedula, nombre, puntaje, grupo, titulos, estado, vulnerabilidad, fecha_inscripcion, base_datos):
        super().__init__(cedula, nombre)
        self.puntaje = puntaje
        self.grupo = grupo
        self.titulos = titulos
        self.estado = estado
        self.vulnerabilidad = vulnerabilidad
        self.fecha_inscripcion = fecha_inscripcion
        self.base_datos = base_datos  

    def rechazar_cupo(self, cupo):
        self.estado = "Rechazado"
        self.base_datos.guardar_estado_aspirante(self.cedula, self.estado)

    def aceptar_cupo(self, cupo):
        self.estado = "Aceptado"
        self.base_datos.guardar_estado_aspirante(self.cedula, self.estado)

    def descripcion(self):
        return f"Aspirante: {self.nombre}"
