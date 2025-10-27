from Reporte import Reporte
from Cargar_datos import cargar_datos

class PeriodoAcademico(Reporte):
    def __init__(self, aspirantes, id_periodo, nombre, fecha_inicio, estado, universidad,
                 lista_carreras, lista_cupos, lista_matriculas):
        super().__init__(aspirantes)  # Atributo heredado de Reporte para generar informes
        self.id_periodo = id_periodo
        self.nombre = nombre
        self.fecha_inicio = fecha_inicio
        self.estado = estado
        self.universidad = universidad
        self.lista_carreras = lista_carreras
        self.lista_cupos = lista_cupos
        self.lista_matriculas = lista_matriculas

    def activar(self):
        pass
    def cerrar(self):
        pass
    def listar_carreras(self):
        pass
    def listar_cupos(self):
        pass
    def listar_matriculas(self):
        pass
    def generar_reporte(self):
        pass
<<<<<<< HEAD:periodo_acádemico.py
    def generar_informe(self):
        # Ejemplo de informe: número de aspirantes que postularon a la universidad de este período
        total = sum(1 for a in self.aspirantes if a[1] == self.universidad)
        aceptados = sum(1 for a in self.aspirantes if a[1] == self.universidad and a[15] == "1")
        porcentaje = (aceptados / total * 100) if total else 0
        return (
            f"=== INFORME PERIODO {self.nombre} ({self.universidad}) ===\n"
            f"Total de aspirantes: {total}\n"
            f"Aceptaron el cupo: {aceptados}\n"
            f"Porcentaje de aceptación: {porcentaje:.2f}%"
        )

if __name__ == "__main__":
    # Cargar datos
    datos = cargar_datos().cargar()

    # Crear un objeto PeriodoAcademico
    periodo = PeriodoAcademico(
        aspirantes=datos,
        id_periodo=1,
        nombre="2025-1",
        fecha_inicio="2025-03-01",
        estado="Activo",
        universidad="UNIVERSIDAD LAYCA ELOY ALFARO DE MANABÍ",
        lista_carreras=["Software"],
        lista_cupos=[10],
        lista_matriculas=[]
    )

    #Generar y mostrar informe
    print(periodo.generar_informe())
=======
>>>>>>> 169aad0c346ed19a082b2ae3f13da942e223cbdc:Periodo_acádemico.py
