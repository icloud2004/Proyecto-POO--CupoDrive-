class Cupo:
    def __init__(self, id_cupo, carrera, estado="Disponible", segmento=None, periodo=None, aspirante=None):
        self.id_cupo = id_cupo
        self.carrera = carrera
        self.estado = estado          # Disponible, Asignado, Aceptado, Liberado
        self.segmento = segmento
        self.periodo = periodo
        self.aspirante = aspirante

    def _aspirante_nombre(self, aspirante):
        try:
            if aspirante is None:
                return ""
            if isinstance(aspirante, dict):
                return (aspirante.get("nombre") or aspirante.get("nombres") or "").strip()
            return getattr(aspirante, "nombre", "") or getattr(aspirante, "nombres", "") or ""
        except Exception:
            return ""

    def _aspirante_puntaje(self, aspirante):
        try:
            if aspirante is None:
                return ""
            if isinstance(aspirante, dict):
                return aspirante.get("puntaje") or aspirante.get("puntaje_postulacion") or aspirante.get("puntaje_post") or ""
            return getattr(aspirante, "puntaje", "") or getattr(aspirante, "puntaje_postulacion", "") or ""
        except Exception:
            return ""

    def asignar_aspirante(self, aspirante):
        if self.estado == "Disponible":
            self.aspirante = aspirante
            self.estado = "Asignado"
            nombre = self._aspirante_nombre(aspirante)
            puntaje = self._aspirante_puntaje(aspirante)
            try:
                if nombre or puntaje != "":
                    print(f" Cupo {self.id_cupo} asignado a {nombre} ({puntaje} puntos).")
                else:
                    print(f" Cupo {self.id_cupo} asignado (aspirante sin nombre/puntaje visibles).")
            except Exception:
                # en caso de que print falle por encoding u otros, no interrumpir
                pass
        else:
            print(f" Cupo {self.id_cupo} ya está ocupado o no disponible.")

    def liberar(self):
        if self.estado in ["Asignado", "Rechazado"]:
            nombre = self._aspirante_nombre(self.aspirante)
            try:
                if nombre:
                    print(f" Cupo {self.id_cupo} liberado (antes asignado a {nombre}).")
                else:
                    print(f" Cupo {self.id_cupo} liberado.")
            except Exception:
                pass
            self.aspirante = None
            self.estado = "Disponible"
        else:
            print(f" No se puede liberar el cupo {self.id_cupo} (estado actual: {self.estado}).")

    def aceptar(self):
        if self.aspirante and self.estado == "Asignado":
            self.estado = "Aceptado"
            nombre = self._aspirante_nombre(self.aspirante)
            try:
                if nombre:
                    print(f" {nombre} aceptó el cupo de {self.carrera}.")
                else:
                    print(f" Aspirante aceptó el cupo de {self.carrera}.")
            except Exception:
                pass
        else:
            print(" No se puede aceptar un cupo sin aspirante asignado o ya aceptado.")

# Ejemplo de uso (solo si se ejecuta como script)
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

    print("\n Caso adicional: liberar cupo asignado...")
    cupo2 = Cupo(id_cupo=2, carrera="Tecnologías de la Información")
    cupo2.asignar_aspirante(aspirante2)
    cupo2.liberar()