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
# Caso de uso
class Aspirante:
    def __init__(self, nombre, puntaje, vulnerabilidad):
        self.nombre = nombre
        self.puntaje = puntaje
        self.vulnerabilidad = vulnerabilidad
segmento1 = Segmento("Mérito Académico", 40, ["puntaje >= 850"])
segmento2 = Segmento("Vulnerabilidad", 30, ["vulnerabilidad == alta"])
segmento3 = Segmento("Población General", 30, ["sin restricción"])

asp1 = Aspirante("Jorge Luis", 890, "media")
asp2 = Aspirante("Ana Belen", 760, "alta")

print(segmento1.verificar_criterios(asp1))
print(segmento2.verificar_criterios(asp2))
print(segmento3.verificar_criterios(asp1))
oferta_total = 100
print(f"Cupos para {segmento1}: {segmento1.calcular_cupos_total(oferta_total)}")
print(f"Cupos para {segmento2}: {segmento2.calcular_cupos_total(oferta_total)}")
print(f"Cupos para {segmento3}: {segmento3.calcular_cupos_total(oferta_total)}")