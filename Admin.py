from Reporte import *
from Persona import Persona

class Administrador:
    def __init__(self, cedula, usuario, contrasena, rol):
        self.cedula = cedula
        self.usuario = usuario
        self.contrasena = contrasena
        self.rol = rol

    def asignar_cupos(self):
        pass

    def liberar_cupos(self):
        pass

    def generar_reporte(self):
        pass

    def modificar_segmento(self):
        pass


class Administrador(Persona):
    def __init__(self, cedula, nombre, usuario, contrasena, rol):
        super().init(cedula, nombre)
        self.usuario = usuario
        self.contrasena = contrasena
        self.rol = rol

    def asignar_cupos(self):
        pass

    def liberar_cupos(self):
        pass

    def generar_reporte(self):
        pass

    def modificar_segmento(self):
        pass

    def descripcion(self):
        return f"Administrador: {self.nombre}"
