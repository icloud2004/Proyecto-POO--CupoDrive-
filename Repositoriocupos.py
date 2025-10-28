from datetime import datetime
class RepositorioCupos:
    def __init__(self):
        self.registro_estados = []
        self.aceptaciones = []

    def actualizar_estado_aspirante(self, aspirante, nuevo_estado):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.registro_estados.append({
            "aspirante": aspirante.nombre,
            "nuevo_estado": nuevo_estado,
            "fecha": fecha
        })
        aspirante.estado = nuevo_estado
        print(f"Estado del aspirante {aspirante.nombre} actualizado a '{nuevo_estado}'.")

    def actualizar_estado_cupo(self, cupo, nuevo_estado):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.registro_estados.append({
            "cupo": cupo.id_cupo,
            "carrera": cupo.carrera,
            "nuevo_estado": nuevo_estado,
            "fecha": fecha
        })
        cupo.estado = nuevo_estado
        print(f"Estado del cupo {cupo.id_cupo} actualizado a '{nuevo_estado}'.")

    def registrar_aceptacion(self, aspirante, cupo, fecha):
        registro = {
            "aspirante": aspirante.nombre,
            "carrera": cupo.carrera,
            "fecha_aceptacion": fecha
        }
        self.aceptaciones.append(registro)
        print(f"Aceptación registrada: {aspirante.nombre} - {cupo.carrera} ({fecha})")

    def mostrar_registros(self):
        print("Historial de actualizaciones")
        for r in self.registro_estados:
            print(r)
# Caso de uso
class Aspirante:
    def __init__(self, nombre):
        self.nombre = nombre
        self.estado = "pendiente"

class Cupo:
    def __init__(self, id_cupo, carrera):
        self.id_cupo = id_cupo
        self.carrera = carrera
        self.estado = "disponible"

repo = RepositorioCupos()
aspirante1 = Aspirante("Jorge Luis")
cupo1 = Cupo("001", "Tecnologia de la informacion")

repo.actualizar_estado_aspirante(aspirante1, "en revisión")
repo.actualizar_estado_cupo(cupo1, "asignado")
repo.registrar_aceptacion(aspirante1, cupo1, datetime.now().strftime("%Y-%m-%d"))
repo.mostrar_registros()