from Cargar_datos import Cargar_datos
from Carrera import Carrera
from Asignación_cupos import Asignacion_cupo
from Admin import Admin
from Aceptacion_cupo import Aceptacion_cupo
from Certificado_aceptacion import Certificado_aceptacion
from Repositoriocupos import RepositorioCupos
from Segmento import Segmento
from Universidad import Universidad
from Periodo_acádemico import Periodo_academico


#EL MAIN LO BASAMOS RESPECTO A LA BASE DE DATOS CSV QUE TENEMOS EN NUESTRO REPOSITORIO.

def main():
    
    print("  SISTEMA AUTOMATIZADO DE ASIGNACIÓN DE CUPOS (CUPODRIVE)")
 

    datos = Cargar_datos("BaseDatos.csv").cargar()

    #Crear universidad y periodo académico
    uni = Universidad(
        id_universidad="102",
        nombre="UNIVERSIDAD LAICA ELOY ALFARO DE MANABÍ",
        direccion="Manta - Ecuador",
        telefono="052-600-123",
        correo="info@uleam.edu.ec",
        estado="Activa"
    )

    periodo = Periodo_academico(
        id_periodo="2025A",
        nombre="Primer Periodo Académico 2025",
        fecha_inicio="2025-01-15",
        estado="Pendiente",
        universidad=uni
    )
    uni.agregar_periodo(periodo)
    periodo.activar()

    #Crear una carrera de ejemplo
    carrera_software = Carrera(id_carrera="001", nombre="Software", oferta_cupos=5)
    uni.agregar_carrera(carrera_software)
    periodo.agregar_carrera(carrera_software)

    #Crear segmentos
    seg_vulnerabilidad = Segmento("Vulnerabilidad", 10, ["alta vulnerabilidad"])
    seg_merito = Segmento("Mérito Académico", 20, ["puntaje >= 850"])
    seg_general = Segmento("Población General", 70, ["todos"])

    carrera_software.agregar_segmento(seg_vulnerabilidad)
    carrera_software.agregar_segmento(seg_merito)
    carrera_software.agregar_segmento(seg_general)

    #Asignar cupos
    asignacion = Asignacion_cupo(carrera_software, datos)
    asignacion.asignar_cupos()