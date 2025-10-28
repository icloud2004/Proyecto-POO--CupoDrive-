class Periodo_academico:

    def __init__(self, id_periodo, nombre, fecha_inicio, estado, universidad):
        self.id_periodo = id_periodo
        self.nombre = nombre
        self.fecha_inicio = fecha_inicio
        self.estado = estado  # Ejemplo: "Activo", "Cerrado"
        self.universidad = universidad
        self.lista_carreras = []
        self.lista_cupos = []
        self.lista_matriculas = []

    def activar(self):
        self.estado = "Activo"
        print(f" Periodo {self.nombre} activado correctamente.")

    def cerrar(self):
        self.estado = "Cerrado"
        print(f" Periodo {self.nombre} cerrado correctamente.")

    def agregar_carrera(self, carrera):
        self.lista_carreras.append(carrera)
        print(f" Carrera '{carrera.nombre}' agregada al periodo {self.nombre}.")

    def listar_carreras(self):
        print(f"\n CARRERAS DEL PERIODO {self.nombre}:")
        for c in self.lista_carreras:
            print(f" - {c.nombre} ({c.oferta_cupos} cupos)")

    def listar_cupos(self):
        print(f"\n CUPOS DISPONIBLES EN EL PERIODO {self.nombre}:")
        total = 0
        for carrera in self.lista_carreras:
            disponibles = len(carrera.obtener_cupos_disponibles())
            total += disponibles
            print(f" - {carrera.nombre}: {disponibles} cupos disponibles")
        print(f" Total general de cupos disponibles: {total}")

    def generar_reporte(self):
        print(f"\n===== REPORTE DEL PERIODO ACADÉMICO {self.nombre} =====")
        print(f"Estado: {self.estado}")
        print(f"Número de carreras: {len(self.lista_carreras)}")
        total_cupos = sum(len(c.cupos) for c in self.lista_carreras)
        print(f"Total de cupos generados: {total_cupos}")

        #Ejemplo caso de uso

if __name__ == "__main__":

    # Clase auxiliar simulada para Carrera
    class Carrera:
        def __init__(self, nombre, oferta_cupos):
            self.nombre = nombre
            self.oferta_cupos = oferta_cupos
            self.cupos = [f"Cupo{i+1}" for i in range(oferta_cupos)]

        def obtener_cupos_disponibles(self):
            return self.cupos

    
    universidad = "Universidad Laica Eloy Alfaro de Manabí"


    periodo = Periodo_academico(
        id_periodo="2025A",
        nombre="Primer Semestre 2025",
        fecha_inicio="2025-03-01",
        estado="Inactivo",
        universidad=universidad
    )


    periodo.activar()

    
    carrera1 = Carrera("Ingeniería en Software", 5)
    carrera2 = Carrera("Tecnologías de la Información", 4)
    carrera3 = Carrera("Administración de Empresas", 3)

    periodo.agregar_carrera(carrera1)
    periodo.agregar_carrera(carrera2)
    periodo.agregar_carrera(carrera3)

    
    periodo.listar_carreras()
    periodo.listar_cupos()


    periodo.generar_reporte()

    periodo.cerrar()