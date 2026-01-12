from Cargar_datos import Cargar_datos
from Carrera import Carrera
from Asignacion_cupos import Asignacion_cupo
from Admin import Administrador
from Aceptacion_cupo import Aceptacion_cupo
from Certificado_aceptacion import Certificado_aceptacion
from Repositoriocupos import RepositorioCupos
from Segmento import Segmento
from Universidad import Universidad
from Periodo_academico import Periodo_academico


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

    #Registrar aceptación del primer aspirante asignado
    if asignacion.asignados:
        primer_aspirante = asignacion.asignados[0]
        primer_cupo = carrera_software.cupos[0]

        aceptacion = Aceptacion_cupo(primer_aspirante, primer_cupo)
        aceptacion.aceptar()

        #Generar certificado
        certificado = Certificado_aceptacion(aceptacion)
        certificado.generar_certificado()

        #Registrar en repositorio
        repo = RepositorioCupos()
        repo.registrar_aceptacion(primer_aspirante, primer_cupo, aceptacion.fecha_aceptacion)
        repo.mostrar_registros()

    #Reporte del administrador
    admin = Administrador("1100456789", "María Zamora", "admin01", "1234", "Administrador General")
    admin.generar_reporte(datos)

    # 8️ Cierre del periodo
    periodo.cerrar()

    print("\n Proceso SAC completado correctamente.\n")
if __name__ == "__main__":
    main()     