import csv
from Aspirante import Aspirante

class Cargar_datos:
    # Esta variable guardará la única instancia de la clase
    _instancia_unica = None

    def __init__(self, ruta_csv="BaseDatos.csv"):
        self.ruta_csv = ruta_csv
        self.aspirantes = []
        self.ya_cargo = False  # Para saber si ya leímos el archivo

    @classmethod
    def obtener_instancia(cls):
        """Este método asegura que solo se cree un objeto (singleton simple)."""
        if cls._instancia_unica is None:
            cls._instancia_unica = cls()
        return cls._instancia_unica

    def cargar(self):
        # Si ya cargamos los datos antes, no los volvemos a leer
        if self.ya_cargo:
            return self.aspirantes

        try:
            with open(self.ruta_csv, newline="", encoding="utf-8") as data:
                lector = csv.reader(data, delimiter=";")
                # Intentar saltar encabezado si existe
                try:
                    next(lector)
                except StopIteration:
                    pass

                # construir conjunto de cédulas ya presentes para evitar duplicados
                existing_ceds = set()
                for ex in self.aspirantes:
                    try:
                        ex_ced = getattr(ex, "cedula", None) if not isinstance(ex, dict) else (ex.get("identificiacion") or ex.get("identificacion") or ex.get("cedula"))
                        if ex_ced:
                            existing_ceds.add(str(ex_ced).strip())
                    except Exception:
                        continue

                for fila in lector:
                    # Si la fila no tiene el número esperado de columnas, ignorarla
                    if not fila or len(fila) < 16:
                        # intentar continuar con la siguiente
                        continue

                    # Desempaquetar según el formato esperado del CSV
                    (
                        ies_id, ies_nombre, identificacion, nombres, apellidos,
                        puntaje_postulacion, prioridad, segmento, nombre_carrera,
                        campus, tipo_cupo, modalidad, nivel, jornada,
                        acepta_estado, fecha_acepta_cupo
                    ) = fila[:16]

                    cedula_from_row = str(identificacion).strip()
                    if cedula_from_row in existing_ceds:
                        # saltar duplicado del CSV respecto a lo ya cargado
                        continue

                    # validar puntaje
                    try:
                        puntaje_val = float(puntaje_postulacion)
                    except Exception:
                        puntaje_val = 0.0

                    aspirante = Aspirante(
                        cedula=identificacion,
                        nombre=f"{nombres} {apellidos}".strip(),
                        puntaje=puntaje_val,
                        grupo=segmento,
                        titulos="Bachiller",
                        estado="Postulado",
                        vulnerabilidad="Alta" if str(segmento).strip() == "1" else "Media",
                        fecha_inscripcion="2025-01-10"
                    )

                    # Guardamos campus en el objeto aspirante para filtrar por sede más tarde
                    try:
                        setattr(aspirante, "campus", campus)
                    except Exception:
                        pass

                    # Guardar prioridad si existe (útil)
                    try:
                        setattr(aspirante, "prioridad", int(prioridad))
                    except Exception:
                        pass

                    # Guardar puntaje_postulacion también como atributo si lo necesitas explícitamente
                    try:
                        setattr(aspirante, "puntaje_postulacion", puntaje_val)
                    except Exception:
                        pass

                    # --- NUEVO: guardar la carrera a la que postuló el aspirante ---
                    try:
                        setattr(aspirante, "carrera_postulada", nombre_carrera)
                        # Alias por compatibilidad (algunas partes del código pueden buscar nombre_carrera)
                        setattr(aspirante, "nombre_carrera", nombre_carrera)
                    except Exception:
                        pass
                    # --------------------------------------------------------------

                    self.aspirantes.append(aspirante)
                    existing_ceds.add(cedula_from_row)

            self.ya_cargo = True  # Marcamos que ya terminó
            return self.aspirantes

        except FileNotFoundError:
            # No existe el archivo; devolver lista vacía
            self.ya_cargo = True
            return self.aspirantes
        except Exception as e:
            # En caso de error inesperado, devolver lo que se haya cargado y loggear si lo deseas
            print("Error cargando CSV:", e)
            self.ya_cargo = True
            return self.aspirantes