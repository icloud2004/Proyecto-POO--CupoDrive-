from Reporte import Reporte
from Cargar_datos import cargar_datos

class Universidad(Reporte):
    def __init__(self, aspirantes, id_universidad, nombre, direccion, telefono, correo, estado,
                 lista_carrera, lista_administradores, lista_periodos, configuracion):
        super().__init__(aspirantes)  # Atributo heredado para reportes
        self.id_universidad = id_universidad
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.correo = correo
        self.estado = estado
        self.lista_carrera = lista_carrera
        self.lista_administradores = lista_administradores
        self.lista_periodos = lista_periodos
        self.configuracion = configuracion

    def generar_informe(self):
        # Ejemplo de informe: número de aspirantes por esta universidad y porcentaje que aceptaron el cupo
        total = sum(1 for a in self.aspirantes if a[1] == self.nombre)
        aceptados = sum(1 for a in self.aspirantes if a[1] == self.nombre and a[15] == "1")
        porcentaje = (aceptados / total * 100) if total else 0
        return (
            f" INFORME UNIVERSIDAD {self.nombre}\n"
            f"Total de aspirantes: {total}\n"
            f"Aceptaron el cupo: {aceptados}\n"
            f"Porcentaje de aceptación: {porcentaje:.2f}%"
        )

#ejemplo de uso
if __name__ == "__main__":
    # Cargar los datos desde el CSV
    datos = cargar_datos().cargar()

    # Crear objeto Universidad
    universidad = Universidad(
        aspirantes=datos,
        id_universidad=102,
        nombre="UNIVERSIDAD LAYCA ELOY ALFARO DE MANABÍ",
        direccion="Av. Principal 123",
        telefono="0991234567",
        correo="info@layca.edu.ec",
        estado="Activo",
        lista_carrera=["Software", "Electrónica"],
        lista_administradores=["admin01", "admin02"],
        lista_periodos=["2025-A", "2025-B"],
        configuracion={"modo": "Presencial"}
    )

    #Genera y mostrar el informe
    print(universidad.generar_informe())

