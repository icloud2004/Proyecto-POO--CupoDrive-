from abc import ABC
from abc import abstractmethod
from Cargar_datos import aspirantes

class Reporte(ABC):
    def __init__(self, aspirantes):
        self.aspirantes = aspirantes

    @abstractmethod
    def generar_informe(self):
        pass

