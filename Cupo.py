class Cupo:
 
    def __init__(self, id_cupo, carrera, estado="Disponible", segmento=None, periodo=None, aspirante=None):
        self.id_cupo = id_cupo
        self.carrera = carrera
        self.estado = estado          # Disponible, Asignado, Aceptado, Liberado
        self.segmento = segmento
        self.periodo = periodo
        self.aspirante = aspirante    

    def asignar_aspirante(self, aspirante):
        if self.estado == "Disponible":
            self.aspirante = aspirante
            self.estado = "Asignado"
            print(f" Cupo {self.id_cupo} asignado a {aspirante.nombre} ({aspirante.puntaje} puntos).")
        else:
            print(f" Cupo {self.id_cupo} ya está ocupado o no disponible.")

    def liberar(self):
        if self.estado in ["Asignado", "Rechazado"]:
            print(f" Cupo {self.id_cupo} liberado (antes asignado a {self.aspirante.nombre}).")
            self.aspirante = None
            self.estado = "Disponible"
        else:
            print(f" No se puede liberar el cupo {self.id_cupo} (estado actual: {self.estado}).")

    def aceptar(self):
        if self.aspirante and self.estado == "Asignado":
            self.estado = "Aceptado"
            print(f" {self.aspirante.nombre} aceptó el cupo de {self.carrera}.")
        else:
            print(" No se puede aceptar un cupo sin aspirante asignado o ya aceptado.")

#Ejemplo caso de uso
if __name__ == "__main__":

    class Aspirante:
        def __init__(self, nombre, puntaje, estado="Postulado"):
            self.nombre = nombre
            self.puntaje = puntaje
            self.estado = estado

    aspirante1 = Aspirante("José Herrera", 910)
    aspirante2 = Aspirante("María López", 870)

    cupo1 = Cupo(id_cupo=1, carrera="Ingeniería en Software", segmento="General", periodo="2025A")

   
    print(" Asignando aspirante al cupo...")
    cupo1.asignar_aspirante(aspirante1)

   
    print("\n Intentando asignar otro aspirante al mismo cupo...")
    cupo1.asignar_aspirante(aspirante2)

   
    print("\n Aspirante acepta el cupo...")
    cupo1.aceptar()

    print("\n Intentando liberar el cupo aceptado...")
    cupo1.liberar()

    #  Crear un segundo cupo para demostrar liberación real
    print("\n Caso adicional: liberar cupo asignado...")
    cupo2 = Cupo(id_cupo=2, carrera="Tecnologías de la Información")
    cupo2.asignar_aspirante(aspirante2)
    cupo2.liberar()
