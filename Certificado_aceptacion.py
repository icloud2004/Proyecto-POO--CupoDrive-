from datetime import datetime
from Aceptacion_cupo import Aceptacion_cupo
from Cupo import Cupo
from Aspirante import Aspirante



class Certificado_aceptacion:
    def __init__(self, aceptacion_cupo):
        self.aceptacion_cupo = aceptacion_cupo #Inyeccion de dependencia

    def generar_certificado(self):
        #Genera e imprime un certificado de aceptación del cupo
        aspirante = self.aceptacion_cupo.aspirante
        cupo = self.aceptacion_cupo.cupo
        fecha = self.aceptacion_cupo.fecha_aceptacion or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if aspirante.estado == "Aceptado":
            print("CERTIFICADO OFICIAL DE ACEPTACIÓN DE CUPO")
            print(f"Aspirante : {aspirante.nombre}")
            print(f"Identificación : {aspirante.cedula}")
            print(f"Carrera : {cupo.carrera}")
            print(f"Fecha de aceptación : {fecha}")
            print("Estado : ACEPTADO ")
        else:
            print(f"No se puede generar certificado, {aspirante.nombre} no ha aceptado el cupo.")
            
#instanciamos un aspirante
aspirante = Aspirante(
        cedula="1350664511",
        nombre="Roler Bolaños",
        puntaje=845.5,
        grupo="2",
        titulos="Bachiller",
        estado="Asignado",          
        vulnerabilidad="Media",
        fecha_inscripcion="2025-01-10"
    )

#instanciamos un ejemplo de cupo
cupo = Cupo(
        id_cupo=101,
        carrera="Ingeniería en Software",
        estado="Asignado",
        segmento="2",
        periodo="2025-A"
    )

# Creamos el proceso de aceptación de cupo
aceptacion = Aceptacion_cupo(aspirante, cupo)
aceptacion.aceptar()  # Cambia estados y asigna fecha

# Generamos el certificado de aceptación
certificado = Certificado_aceptacion(aceptacion)
certificado.generar_certificado()