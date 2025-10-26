class Aspirante:
    
    #Constrtuctor
    def __init__(self, id_aspirante, cedula, nombre, grupo, titulos, estado, vulnerabilidad, fecha_inscripción):
        self.id_aspirante = id_aspirante
        self.cedula = cedula
        self.nombre = nombre
        self.grupo = grupo
        self.titulos = titulos
        self.estado = estado
        self.vulnerabilidad = vulnerabilidad
        self.fecha_inscripcion = fecha_inscripción
    
    def rechazar_cupo(self,cupo):
        pass
    
    def aceptar_cupo(self,cupo):
        pass
    
    def matricular(self,carrera):
        pass
    
