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
