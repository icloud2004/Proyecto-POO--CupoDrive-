from abc import ABC, abstractmethod
import random
from Cupo import Cupo

# =========================
# INTERFAZ STRATEGY
# =========================
class AssignmentStrategy(ABC):

    @abstractmethod
    def assign(self, carrera, aspirantes):
        """Devuelve lista de aspirantes asignados"""
        pass

    def resolver_empates(self, empatados, cupos_disponibles):
        """
        Método por defecto.
        Las estrategias pueden sobrescribirlo.
        """
        return empatados[:cupos_disponibles]


# =========================
# HELPERS COMUNES
# =========================
def _postulados_para_carrera(carrera, aspirantes):
    return [
        a for a in aspirantes
        if (a.carrera_asignada is None or a.carrera_asignada == carrera.nombre)
        and getattr(a, "estado", "") == "Postulado"
    ]


def _asignar_a_lista(cupos, aspirantes_seleccionados, carrera):
    asignados = []
    for cupo, aspirante in zip(cupos, aspirantes_seleccionados):
        cupo.asignar_aspirante(aspirante)
        aspirante.carrera_asignada = carrera.nombre
        aspirante.estado = "Asignado"
        asignados.append(aspirante)
    return asignados


# =========================
# ESTRATEGIAS CONCRETAS
# =========================
class MeritStrategy(AssignmentStrategy):

    def assign(self, carrera, aspirantes):
        postulados = _postulados_para_carrera(carrera, aspirantes)
        ordenados = sorted(
            postulados,
            key=lambda x: getattr(x, "puntaje", 0),
            reverse=True
        )

        cupos = carrera.obtener_cupos_disponibles()
        asignados = []
        i = 0

        while i < len(ordenados) and len(asignados) < len(cupos):
            mismo_puntaje = [ordenados[i]]
            j = i + 1

            while j < len(ordenados) and ordenados[j].puntaje == ordenados[i].puntaje:
                mismo_puntaje.append(ordenados[j])
                j += 1

            espacios = len(cupos) - len(asignados)

            if len(mismo_puntaje) <= espacios:
                asignados.extend(mismo_puntaje)
            else:
                seleccionados = self.resolver_empates(mismo_puntaje, espacios)
                asignados.extend(seleccionados)

            i = j

        return _asignar_a_lista(cupos, asignados, carrera)

    def resolver_empates(self, empatados, cupos_disponibles):
        # Desempate por sorteo
        return random.sample(empatados, cupos_disponibles)


class LotteryStrategy(AssignmentStrategy):

    def assign(self, carrera, aspirantes):
        postulados = _postulados_para_carrera(carrera, aspirantes)
        cupos = carrera.obtener_cupos_disponibles()

        n = min(len(cupos), len(postulados))
        if n == 0:
            return []

        seleccion = random.sample(postulados, k=n)
        return _asignar_a_lista(cupos, seleccion, carrera)

    def resolver_empates(self, empatados, cupos_disponibles):
        return random.sample(empatados, cupos_disponibles)


class SegmentQuotaStrategy(AssignmentStrategy):

    def __init__(self):
        super().__init__()

    def _es_politica(self, seg):
        """
        Detecta si un segmento representa 'Política de Cuotas' por su nombre.
        """
        nombre = getattr(seg, "nombre", "") or (seg.get("nombre") if isinstance(seg, dict) else "")
        nombre = str(nombre).lower()
        return ("política" in nombre) or ("politica" in nombre) or ("cuota" in nombre)

    def _obtener_prioridad(self, a):
        """
        Intenta obtener la prioridad del aspirante de varias formas.
        Devuelve int (mayor valor = peor prioridad). Si no está -> 999
        """
        p = getattr(a, "prioridad", None)
        try:
            if p is None:
                p = int(getattr(a, "prioridad", 999))
            return int(p)
        except Exception:
            try:
                return int(float(str(p)))
            except Exception:
                return 999

    def assign(self, carrera, aspirantes):
        cupos = [c for c in carrera.cupos if c.estado == "Disponible"]
        oferta = getattr(carrera, "oferta_cupos", len(cupos))
        asignados = []
        idx = 0

        for seg in getattr(carrera, "segmentos", []):
            cuota = seg.calcular_cupos_total(oferta)

            # FILTRADO MEJORADO: si el segmento es "Política de Cuotas" exigimos prioridad > 1
            candidatos = []
            for a in aspirantes:
                if getattr(a, "estado", "") != "Postulado":
                    continue
                try:
                    cumple = seg.verificar_criterios(a)
                except Exception:
                    # si seg.verificar_criterios falla por estructura del aspirante, asumimos False
                    cumple = False
                if not cumple:
                    continue

                if self._es_politica(seg):
                    # filtro estricto para política de cuotas:
                    # - prioridad > 1 OR tipo_cupo == 2 OR segmento==2 (según datos CSV)
                    prioridad = self._obtener_prioridad(a)
                    tipo_cupo = getattr(a, "tipo_cupo", None) or getattr(a, "segmento", None) or ""
                    tipo_cupo_str = str(tipo_cupo).strip()
                    if not (prioridad > 1 or tipo_cupo_str == "2"):
                        # no cumple la política de cuotas
                        continue

                candidatos.append(a)

            candidatos = sorted(
                candidatos,
                key=lambda x: getattr(x, "puntaje", 0),
                reverse=True
            )

            espacios = min(cuota, len(cupos) - idx)

            if espacios <= 0:
                break

            if len(candidatos) <= espacios:
                asignados += _asignar_a_lista(
                    cupos[idx:idx + len(candidatos)],
                    candidatos,
                    carrera
                )
                idx += len(candidatos)
            else:
                seleccionados = self.resolver_empates(candidatos, espacios)
                asignados += _asignar_a_lista(
                    cupos[idx:idx + espacios],
                    seleccionados,
                    carrera
                )
                idx += espacios

        # Completar cupos restantes por mérito
        restantes = cupos[idx:]
        if restantes:
            postulados = _postulados_para_carrera(carrera, aspirantes)
            postulados_rest = sorted(
                [a for a in postulados if a not in asignados],
                key=lambda x: getattr(x, "puntaje", 0),
                reverse=True
            )
            asignados += _asignar_a_lista(restantes, postulados_rest, carrera)

        return asignados


# =========================
# CONTEXTO
# =========================
class Asignacion_cupo:

    def __init__(self, carrera, lista_aspirantes, strategy: AssignmentStrategy = None):
        self.carrera = carrera
        self.lista_aspirantes = lista_aspirantes
        self.strategy = strategy or MeritStrategy()
        self.asignados = []

    def asignar_cupos(self):
        print(f"\nASIGNACIÓN - {self.carrera.nombre}")
        self.asignados = self.strategy.assign(
            self.carrera,
            self.lista_aspirantes
        )
        for i, a in enumerate(self.asignados, 1):
            print(f"{i}. {a.nombre} - Puntaje: {getattr(a, 'puntaje', 'N/A')}")
        return self.asignados

    def liberar_cupos(self):
        for c in self.carrera.cupos:
            if c.estado == "Asignado" and getattr(c, "aspirante", None) \
               and c.aspirante.estado == "Rechazado":
                c.liberar()
                print(f"Cupo liberado: {c.id_cupo} ({c.carrera})")


# =========================
# EJEMPLO DE USO
# =========================
if __name__ == "__main__":

    class Aspirante:
        def __init__(self, nombre, puntaje, prioridad=1, tipo_cupo=None):
            self.nombre = nombre
            self.puntaje = puntaje
            self.estado = "Postulado"
            self.carrera_asignada = None
            self.prioridad = prioridad
            self.tipo_cupo = tipo_cupo

    class Carrera:
        def __init__(self, nombre, n):
            self.nombre = nombre
            self.cupos = [
                Cupo(i + 1, nombre, "Disponible", "G", "2025A")
                for i in range(n)
            ]
            self.oferta_cupos = n
            # ejemplo de segmentos: merito + politica
            from Segmento import Segmento
            self.segmentos = [
                Segmento("Mérito Académico", 70, ["puntaje >= 850"]),
                Segmento("Política de Cuotas", 30, ["prioridad > 1"])
            ]

        def obtener_cupos_disponibles(self):
            return [c for c in self.cupos if c.estado == "Disponible"]

    aspirantes = [
        Aspirante("Ana", 900, prioridad=1),
        Aspirante("Luis", 900, prioridad=2, tipo_cupo="2"),
        Aspirante("Carlos", 880, prioridad=2),
        Aspirante("Maria", 870, prioridad=1)
    ]

    carrera = Carrera("Software", 2)

    contexto = Asignacion_cupo(carrera, aspirantes, SegmentQuotaStrategy())
    contexto.asignar_cupos()