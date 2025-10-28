from Persona import Persona

class Administrador(Persona):

    def __init__(self, cedula, nombre, usuario, contrasena, rol):
        super().__init__(cedula, nombre)
        self.usuario = usuario
        self.contrasena = contrasena
        self.rol = rol  # Ejemplo: "Administrador general"

    def generar_reporte(self, lista_aspirantes):
        """Genera un reporte básico del proceso de asignación."""
        total = len(lista_aspirantes)
        aceptados = sum(1 for a in lista_aspirantes if a.estado == "Aceptado")
        rechazados = sum(1 for a in lista_aspirantes if a.estado == "Rechazado")
        sin_respuesta = total - (aceptados + rechazados)

        reporte = (
            "\n===== REPORTE GENERAL DEL PROCESO ASIGNACION DE CUPO =====\n"
            f"Administrador: {self.nombre}\n"
            f"Rol: {self.rol}\n"
            f"Total de aspirantes: {total}\n"
            f"Aceptaron el cupo: {aceptados}\n"
            f"Rechazaron el cupo: {rechazados}\n"
            f"Sin respuesta: {sin_respuesta}\n"
            f"Porcentaje de aceptación: {(aceptados / total) * 100:.2f}%\n"
            "===========================================\n"
        )
        print(reporte)
        return reporte

    def descripcion(self):
        """Descripción simple del administrador."""
        return f"Administrador: {self.nombre} ({self.rol})"

#Ejemplo caso de uso
if __name__ == "__main__":

    # Clase auxiliar: simulamos un Aspirante con solo nombre y estado
    class Aspirante:
        def __init__(self, nombre, estado):
            self.nombre = nombre
            self.estado = estado

    
    aspirantes = [
        Aspirante("José Herrera", "Aceptado"),
        Aspirante("María López", "Rechazado"),
        Aspirante("Carlos Paredes", "Aceptado"),
        Aspirante("Diana Pérez", "Postulado"),
        Aspirante("Ana Torres", "Aceptado"),
    ]

    # Instancia de clase
    admin = Administrador(
        cedula="1100234567",
        nombre="María Zamora",
        usuario="admin01",
        contrasena="1234",
        rol="Administrador General"
    )

    # Mostrar descripción y generar el reporte
    print(admin.descripcion())
    admin.generar_reporte(aspirantes)