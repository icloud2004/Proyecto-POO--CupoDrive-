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