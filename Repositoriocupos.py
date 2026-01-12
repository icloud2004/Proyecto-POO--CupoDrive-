# Repositoriocupos.py
# Adaptador que utiliza persistencia JSON (persistencia.py)
import traceback
from typing import List, Optional

from persistencia import save_cupos, load_cupos, save_cupos_from_records

class RepositorioCupos:
    def __init__(self, carreras_list_ref: Optional[List] = None):
        """
        carreras_list_ref: referencia (opcional) a la lista global de carreras en memoria.
        Si se pasa, el repositorio puede aplicar los estados cargados desde JSON
        directamente a las instancias Carrera/Cupo en memoria.
        """
        self.carreras_ref = carreras_list_ref
        # cargamos registros persistidos (lista de dicts)
        try:
            self._persisted = load_cupos() or []
        except Exception:
            self._persisted = []
        # Si se pasó la referencia a carreras, intentamos mapear los estados a objetos
        if self.carreras_ref:
            try:
                self._apply_persisted_to_carreras()
            except Exception:
                traceback.print_exc()

    def _apply_persisted_to_carreras(self):
        """Intenta mapear registros persisted (dicts) a objetos Carrera/Cupo por id_cupo."""
        if not self.carreras_ref:
            return
        # índice por id_cupo para búsqueda rápida
        idx = { str(rec.get("id_cupo","")): rec for rec in self._persisted }
        for carrera in self.carreras_ref:
            for cup in getattr(carrera, "cupos", []):
                cid = str(getattr(cup, "id_cupo", "") or "")
                rec = idx.get(cid)
                if not rec:
                    continue
                # aplicar estado si está en el registro persistido
                try:
                    estado_rec = rec.get("estado", "")
                    if estado_rec:
                        try:
                            setattr(cup, "estado", estado_rec)
                        except Exception:
                            # intentar asignación alternativa
                            cup.estado = estado_rec
                except Exception:
                    continue

    # ---------- Operaciones públicas ----------
    def actualizar_estado_cupo(self, cupo, nuevo_estado: str):
        """
        Actualiza el estado de un cupo en memoria y persiste el cambio.
        cupo: objeto Cupo (o dict con keys id_cupo, estado, aspirante)
        """
        id_cupo = str(getattr(cupo, "id_cupo", "") if not isinstance(cupo, dict) else cupo.get("id_cupo", ""))
        aspir_ced = ""
        aspir = getattr(cupo, "aspirante", None) if not isinstance(cupo, dict) else cupo.get("aspirante")
        if aspir:
            try:
                aspir_ced = getattr(aspir, "cedula", "") if not isinstance(aspir, dict) else (aspir.get("cedula") or aspir.get("identificacion") or "")
            except Exception:
                aspir_ced = ""

        # actualizar en persisted (si ya existía) o añadir nuevo
        updated = False
        for rec in self._persisted:
            if str(rec.get("id_cupo", "")) == id_cupo:
                rec["estado"] = nuevo_estado
                rec["aspirante_cedula"] = aspir_ced
                updated = True
                break
        if not updated:
            self._persisted.append({
                "carrera_id": "",
                "carrera_nombre": "",
                "id_cupo": id_cupo,
                "estado": nuevo_estado,
                "aspirante_cedula": aspir_ced
            })

        # también actualizar el objeto cupo en memoria si tiene atributo estado
        try:
            if not isinstance(cupo, dict):
                setattr(cupo, "estado", nuevo_estado)
        except Exception:
            pass

        # persistir a disco: preferimos serializar desde carreras_ref si está disponible
        try:
            if self.carreras_ref:
                save_cupos(self.carreras_ref)
            else:
                save_cupos_from_records(self._persisted)
        except Exception:
            traceback.print_exc()

    def guardar_cupo(self, cupo, carrera=None):
        """Guardar/añadir un cupo (persistir)."""
        id_cupo = str(getattr(cupo, "id_cupo", "") if not isinstance(cupo, dict) else cupo.get("id_cupo", ""))
        estado = getattr(cupo, "estado", "") if not isinstance(cupo, dict) else cupo.get("estado", "")
        aspir_ced = ""
        aspir = getattr(cupo, "aspirante", None) if not isinstance(cupo, dict) else cupo.get("aspirante")
        if aspir:
            if isinstance(aspir, dict):
                aspir_ced = aspir.get("cedula") or aspir.get("identificacion") or ""
            else:
                aspir_ced = getattr(aspir, "cedula", "") or ""

        rec = {
            "carrera_id": getattr(carrera, "id_carrera", "") if carrera is not None else "",
            "carrera_nombre": getattr(carrera, "nombre", "") if carrera is not None else "",
            "id_cupo": id_cupo,
            "estado": estado,
            "aspirante_cedula": aspir_ced
        }
        # reemplazar si ya existe
        for i, r in enumerate(self._persisted):
            if str(r.get("id_cupo", "")) == id_cupo:
                self._persisted[i] = rec
                break
        else:
            self._persisted.append(rec)

        # persistir
        try:
            if self.carreras_ref:
                save_cupos(self.carreras_ref)
            else:
                save_cupos_from_records(self._persisted)
        except Exception:
            traceback.print_exc()

    def eliminar_cupo(self, cupo):
        id_cupo = str(getattr(cupo, "id_cupo", "") if not isinstance(cupo, dict) else cupo.get("id_cupo", ""))
        self._persisted = [r for r in self._persisted if str(r.get("id_cupo","")) != id_cupo]
        try:
            if self.carreras_ref:
                save_cupos(self.carreras_ref)
            else:
                save_cupos_from_records(self._persisted)
        except Exception:
            traceback.print_exc()

    def save_all(self):
        """Forzar persistencia al estado actual de carreras_ref (si existe)."""
        try:
            if self.carreras_ref:
                save_cupos(self.carreras_ref)
            else:
                save_cupos_from_records(self._persisted)
        except Exception:
            traceback.print_exc()
