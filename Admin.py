from Reporte import Reporte
from Cargar_datos import cargar_datos

class Administrador(Reporte):
    def __init__(self, aspirantes, cedula, usuario, contrasena, rol):
        super().__init__(aspirantes)
        self.cedula = cedula
        self.usuario = usuario
        self.contrasena = contrasena
        self.rol = rol

    def generar_informe(self):
        total = len(self.aspirantes)
        cupos_aceptados = sum(1 for a in self.aspirantes if a[15] == "1")
        no_aceptados = total - cupos_aceptados
        return (
            "=== INFORME DEL ADMINISTRADOR ===\n"
            f"Total de aspirantes: {total}\n"
            f"Cupos aceptados: {cupos_aceptados}\n"
            f"No aceptaron el cupo: {no_aceptados}\n"
            f"Porcentaje de aceptación: {(cupos_aceptados / total) * 100:.2f}%"
        )

# ------------------------------
# EJEMPLO DE USO
# ------------------------------
if __name__ == "__main__":
    datos = cargar_datos().cargar()

    # ✅ Instanciamos la subclase, NO la clase abstracta
    admin = Administrador(
        aspirantes=datos,
        cedula="1100456789",
        usuario="admin01",
        contrasena="1234",
        rol="Administrador"
    )

    print(admin.generar_informe())
