class Cupo:
    def __init__(self, id_cupo, carrera, estado, segmento, periodo, aspirante=None):
        self.id_cupo = id_cupo
        self.carrera = carrera
        self.estado = estado
        self.segmento = segmento
        self.periodo = periodo
        self.aspirante = aspirante

    def asignar_aspirantes(self, aspirantes):
        pass

    def liberar(self):
        pass

    def aceptar(self):
        pass