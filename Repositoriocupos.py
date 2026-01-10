import os
import json
from datetime import datetime

class RepositorioCupos:
    def __init__(self, storage_dir='data'):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.registro_estados = self._load_json('registro_estados.json')
        self.aceptaciones = self._load_json('aceptaciones.json')

    def _path(self, filename):
        return os.path.join(self.storage_dir, filename)

    def _load_json(self, filename):
        path = self._path(filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_json(self, filename, data):
        path = self._path(filename)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[RepositorioCupos] Error guardando {filename}: {e}")

    def actualizar_estado_aspirante(self, aspirante, nuevo_estado):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "tipo": "aspirante",
            "aspirante": getattr(aspirante, 'nombre', ''),
            "cedula": getattr(aspirante, 'cedula', ''),
            "nuevo_estado": nuevo_estado,
            "fecha": fecha
        }
        self.registro_estados.append(entry)
        try:
            aspirante.estado = nuevo_estado
        except Exception:
            pass
        self._save_json('registro_estados.json', self.registro_estados)
        print(f"Estado del aspirante {getattr(aspirante,'nombre','')} actualizado a '{nuevo_estado}'.")

    def actualizar_estado_cupo(self, cupo, nuevo_estado):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "tipo": "cupo",
            "cupo": getattr(cupo, 'id_cupo', ''),
            "carrera": getattr(cupo, 'carrera', ''),
            "nuevo_estado": nuevo_estado,
            "fecha": fecha
        }
        self.registro_estados.append(entry)
        try:
            cupo.estado = nuevo_estado
        except Exception:
            pass
        self._save_json('registro_estados.json', self.registro_estados)
        print(f"Estado del cupo {getattr(cupo,'id_cupo','')} actualizado a '{nuevo_estado}'.")

    def registrar_aceptacion(self, aspirante, cupo, fecha):
        registro = {
            "aspirante": getattr(aspirante, 'nombre', ''),
            "cedula": getattr(aspirante, 'cedula', ''),
            "carrera": getattr(cupo, 'carrera', ''),
            "id_cupo": getattr(cupo, 'id_cupo', ''),
            "fecha_aceptacion": fecha
        }
        self.aceptaciones.append(registro)
        self._save_json('aceptaciones.json', self.aceptaciones)
        print(f"Aceptación registrada: {getattr(aspirante,'nombre','')} - {getattr(cupo,'carrera','')} ({fecha})")

    def mostrar_registros(self):
        print("Historial de actualizaciones")
        for r in self.registro_estados:
            print(r)

    def reasignar_cupo(self, cupo, aspirantes, carrera):
        """
        Intentar reasignar un cupo liberado al siguiente postulante por mérito.
        Retorna el aspirante asignado o None si no hay postulantes.
        """
        if getattr(cupo, 'estado', '') != 'Disponible':
            return None

        candidatos = [a for a in aspirantes
                      if (getattr(a, 'carrera_asignada', None) is None or getattr(a, 'carrera_asignada', '') == carrera.nombre)
                      and getattr(a, 'estado', '') == 'Postulado']
        if not candidatos:
            return None

        candidatos = sorted(candidatos, key=lambda x: getattr(x, 'puntaje', 0), reverse=True)
        seleccionado = candidatos[0]

        try:
            cupo.asignar_aspirante(seleccionado)
        except Exception:
            cupo.aspirante = seleccionado
            cupo.estado = 'Asignado'
        seleccionado.carrera_asignada = carrera.nombre
        seleccionado.estado = 'Asignado'

        self.actualizar_estado_aspirante(seleccionado, 'Asignado')
        self.actualizar_estado_cupo(cupo, 'Asignado')

        print(f"Cupo {getattr(cupo,'id_cupo','')} reasignado a {getattr(seleccionado,'nombre','') }.")
        return seleccionado

    def assign_by_segments(self, carrera, aspirantes, segmentos=None):
        """
        Asigna cupos a aspirantes usando la política de segmentos (cuotas).
        - carrera: objeto Carrera con cupos y atributo segmentos (lista de Segmento)
        - aspirantes: lista de objetos Aspirante
        - segmentos: opcional lista de Segmento (si None, usa carrera.segmentos)

        Retorna un resumen dict con asignaciones por segmento y sobrantes.
        """
        segmentos = segmentos if segmentos is not None else getattr(carrera, 'segmentos', [])
        resumen = {"by_segment": [], "filled": [], "remaining_cupos": 0}

        if not segmentos:
            return {"error": "La carrera no tiene segmentos configurados."}

        oferta_total = getattr(carrera, 'oferta_cupos', len(getattr(carrera, 'cupos', [])))

        # Para cada segmento, calcular y asignar
        for seg in segmentos:
            cupos_seg = seg.calcular_cupos_total(oferta_total)
            # candidatos elegibles: Postulado y que cumplan criterios
            candidatos = [a for a in aspirantes if getattr(a, 'estado', '') == 'Postulado' and seg.verificar_criterios(a)]
            candidatos = sorted(candidatos, key=lambda x: getattr(x, 'puntaje', 0), reverse=True)

            asignados_seg = []
            for _ in range(min(cupos_seg, len(candidatos))):
                # obtener primer cupo disponible
                disponibles = carrera.obtener_cupos_disponibles()
                if not disponibles:
                    break
                cupo = disponibles[0]
                aspirante = candidatos.pop(0)
                try:
                    cupo.asignar_aspirante(aspirante)
                except Exception:
                    cupo.aspirante = aspirante
                    cupo.estado = 'Asignado'
                aspirante.carrera_asignada = carrera.nombre
                aspirante.estado = 'Asignado'
                self.actualizar_estado_aspirante(aspirante, 'Asignado')
                self.actualizar_estado_cupo(cupo, 'Asignado')
                asignados_seg.append({"cupo": getattr(cupo,'id_cupo',''), "cedula": getattr(aspirante,'cedula',''), "nombre": getattr(aspirante,'nombre','')})

            resumen['by_segment'].append({"segmento": seg.nombre, "porcentaje": seg.porcentaje, "asignados": asignados_seg})

        # Si quedan cupos disponibles, llenar por mérito con postulados restantes
        disponibles_final = carrera.obtener_cupos_disponibles()
        postulados_restantes = [a for a in aspirantes if getattr(a, 'estado', '') == 'Postulado']
        postulados_restantes = sorted(postulados_restantes, key=lambda x: getattr(x, 'puntaje', 0), reverse=True)

        filled = []
        for aspirante in postulados_restantes:
            if not disponibles_final:
                break
            cupo = disponibles_final.pop(0)
            try:
                cupo.asignar_aspirante(aspirante)
            except Exception:
                cupo.aspirante = aspirante
                cupo.estado = 'Asignado'
            aspirante.carrera_asignada = carrera.nombre
            aspirante.estado = 'Asignado'
            self.actualizar_estado_aspirante(aspirante, 'Asignado')
            self.actualizar_estado_cupo(cupo, 'Asignado')
            filled.append({"cupo": getattr(cupo,'id_cupo',''), "cedula": getattr(aspirante,'cedula',''), "nombre": getattr(aspirante,'nombre','')})

        resumen['filled'] = filled
        resumen['remaining_cupos'] = len(carrera.obtener_cupos_disponibles())
        return resumen
