from Cupo import Cupo
class Asignacion_cupo:
 
    def __init__(self, carrera, lista_aspirantes):
        self.carrera = carrera  # Inyección de dependencia
        self.lista_aspirantes = lista_aspirantes
        self.asignados = []

    def asignar_cupos(self):

        print(f"\n====================================")
        print(f"ASIGNACIÓN PARA CARRERA: {self.carrera.nombre}")
        print(f"====================================")

        # 1️ Filtrar aspirantes válidos
        aspirantes_carrera = [
            a for a in self.lista_aspirantes
            if (a.carrera_asignada is None or a.carrera_asignada == self.carrera.nombre)
            and a.estado == "Postulado"
        ]

        # 2️ Ordenar por puntaje (de mayor a menor)
        aspirantes_ordenados = sorted(aspirantes_carrera, key=lambda x: x.puntaje, reverse=True)

        # 3️ Cupos disponibles
        cupos_disponibles = self.carrera.obtener_cupos_disponibles()
        cantidad = len(cupos_disponibles)

        print(f"Cupos disponibles: {cantidad}")
        print("Cupos asignados:\n")

        # 4️ Asignar cupos según el orden de mérito
        for i in range(min(cantidad, len(aspirantes_ordenados))):
            aspirante = aspirantes_ordenados[i]
            cupo = cupos_disponibles[i]
            cupo.asignar_aspirante(aspirante)
            aspirante.carrera_asignada = self.carrera.nombre
            aspirante.estado = "Asignado"
            self.asignados.append(aspirante)

        # 5️ Mostrar resultados
        for i, a in enumerate(self.asignados, 1):
            print(f"{i}. {a.nombre} - Puntaje: {a.puntaje}")

    def resolver_empates(self):
        print(" Resolviendo empates (versión simplificada)")
        # En una versión avanzada del proyecto se usaran criterios mas avanzados y especificos

    def liberar_cupos(self):
        """Libera los cupos no aceptados."""
        for c in self.carrera.cupos:
            if c.estado == "Asignado" and c.aspirante.estado == "Rechazado":
                c.liberar()
                print(f" Cupo liberado: {c.id_cupo} ({c.carrera})")

#Ejemplo de caso de uso
if __name__ == "__main__":

    # Clases auxiliares simuladas
    class Aspirante:
        def __init__(self, nombre, puntaje, estado="Postulado"):
            self.nombre = nombre
            self.puntaje = puntaje
            self.estado = estado
            self.carrera_asignada = None

    class Carrera:
        def __init__(self, nombre, cupos_disponibles):
            self.nombre = nombre
            self.cupos = [Cupo(i + 1, nombre, "Disponible", "General", "2025A") for i in range(cupos_disponibles)]

        def obtener_cupos_disponibles(self):
            return [c for c in self.cupos if c.estado == "Disponible"]

    
    aspirantes = [
        Aspirante("José Herrera", 910),
        Aspirante("María López", 875),
        Aspirante("Carlos Paredes", 900),
        Aspirante("Diana Pérez", 830),
        Aspirante("Ana Torres", 870),
    ]

    
    carrera_software = Carrera("Ingeniería en Software", cupos_disponibles=3)

    asignacion = Asignacion_cupo(carrera_software, aspirantes)

    asignacion.asignar_cupos()

    # Mostrar resumen final
    print("\n Asignación finalizada.\nAspirantes asignados:")
    for a in asignacion.asignados:
        print(f"- {a.nombre} ({a.puntaje} puntos) → {a.carrera_asignada}")