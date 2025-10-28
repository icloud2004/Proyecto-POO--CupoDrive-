class Universidad:
    def __init__(self, id_universidad, nombre, direccion, telefono, correo, estado):
        self.id_universidad = id_universidad
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.correo = correo
        self.estado = estado
        self.lista_carreras = []
        self.lista_administradores = []
        self.lista_periodos = []

    def agregar_carrera(self, carrera):
        self.lista_carreras.append(carrera)
        print(f"Carrera '{carrera.nombre}' agregada a la universidad {self.nombre}.")

    def eliminar_carrera(self, nombre_carrera):
        for c in self.lista_carreras:
            if c.nombre.lower() == nombre_carrera.lower():
                self.lista_carreras.remove(c)
                print(f"Carrera '{nombre_carrera}' eliminada.")
                return
        print(f"No se encontró la carrera '{nombre_carrera}' para eliminar.")

    def listar_carreras(self):
        print(f"Carreras de la {self.nombre}:")
        for c in self.lista_carreras:
            print(f" - {c.nombre} ({c.oferta_cupos} cupos)")

    def agregar_administrador(self, admin):
        self.lista_administradores.append(admin)
        print(f"Administrador '{admin.nombre}' agregado correctamente.")

    def agregar_periodo(self, periodo):
        self.lista_periodos.append(periodo)
        print(f"Periodo '{periodo.nombre}' agregado a la universidad {self.nombre}.")

    def listar_periodos(self):
        print(f"Periodos academicos de {self.nombre}:")
        for p in self.lista_periodos:
            print(f" - {p.nombre} ({p.estado})")

    def consultar_estado(self):
        print(f"Universidad {self.nombre} está actualmente: {self.estado}")

    def generar_reporte(self):
        print(f"REPORTE GENERAL DE {self.nombre}")
        print(f"Dirección: {self.direccion}")
        print(f"Teléfono: {self.telefono}")
        print(f"Correo: {self.correo}")
        print(f"Estado: {self.estado}")
        print(f"Total carreras: {len(self.lista_carreras)}")
        print(f"Total administradores: {len(self.lista_administradores)}")
        print(f"Total periodos: {len(self.lista_periodos)}")
# Caso de uso
if __name__ == "__main__":
 class Carrera:
    def __init__(self, nombre, oferta_cupos):
        self.nombre = nombre
        self.oferta_cupos = oferta_cupos

 class Administrador:
    def __init__(self, nombre):
        self.nombre = nombre

 class Periodo:
    def __init__(self, nombre, estado):
        self.nombre = nombre
        self.estado = estado

 uni = Universidad("01", "Universidad Layca Eloy Alfaro de Manabi ", "Av. Circunvalacion", "0999999999", "info@uleam.edu.ec", "Activa")

 c1 = Carrera("Ingeniería en Software", 120)
 c2 = Carrera("Diseño Gráfico", 80)
 admin1 = Administrador("Jorge Luis")
 p1 = Periodo("Periodo 2025-2", "En curso")

 uni.agregar_carrera(c1)
 uni.agregar_carrera(c2)
 uni.listar_carreras()

 uni.eliminar_carrera("Diseño Gráfico")
 uni.listar_carreras()

 uni.agregar_administrador(admin1)
 uni.agregar_periodo(p1)
 uni.listar_periodos()

 uni.consultar_estado()
 uni.generar_reporte()