from abc import abstractmethod
from abc import ABCMeta

class Reporte(ABCMeta):
    @abstractmethod
    def generar_reporte():
        pass