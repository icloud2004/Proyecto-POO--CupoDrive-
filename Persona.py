from abc import ABC, abstractmethod
class Persona(ABC):
    def __init__(self, cedula, nombre):
        self.cedula = cedula
        self.nombre = nombre

    @abstractmethod
    def descripcion(self):
        pass
# Caso de uso
class Estudiante(Persona):
    def __init__(self, cedula, nombre, carrera):
        super().__init__(cedula, nombre)
        self.carrera = carrera
    def descripcion(self):
        return (f"{self.nombre} con cédula {self.cedula} es estudiante de {self.carrera}.")
    
estudiante1 = Estudiante("123456784", "Jorge Luis", "Tecnologia de la informacion")
print(estudiante1.descripcion())