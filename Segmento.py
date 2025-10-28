class Segmento:
    def __init__(self, nombre, porcentaje, criterios):
        self.nombre = nombre
        self.porcentaje = float(porcentaje)
        self.criterios = criterios

    def verificar_criterios(self, aspirante):
        if self.nombre.lower() in ["vulnerabilidad", "grupo vulnerable"]:
            return aspirante.vulnerabilidad.lower() == "alta"
        elif self.nombre.lower() in ["mérito", "mérito académico"]:
            return aspirante.puntaje >= 850
        elif self.nombre.lower() == "población general":
            return True
        else:
            return False

    def calcular_cupos_total(self, oferta_total):
        cupos_segmento = int((self.porcentaje / 100) * oferta_total)
        return cupos_segmento

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje}%)"