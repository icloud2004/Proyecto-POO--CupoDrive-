from abc import ABC, abstractmethod
class Persona(ABC):
    def __init__(self, cedula, nombre):
        self.cedula = cedula
        self.nombre = nombre

    @abstractmethod
    def descripcion(self):
        pass