from abc import ABC, abstractmethod
class Persona(ABC):
    #Implementa encapsulamiento
    def __init__(self, cedula, nombre):
        self.__cedula = cedula
        self.__nombre = nombre 
    @property
    def cedula(self):
        return self.__cedula
    @property
    def nombre(self):
        return self.__nombre

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
if __name__ == "__main__":
 estudiante1 = Estudiante("123456784", "Jorge Luis", "Tecnologia de la informacion")
 print(estudiante1.descripcion())