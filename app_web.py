from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
import os

# Importar clases del repo
from Cargar_datos import Cargar_datos
from Cargar_carrera import CargarCarreras
from Carrera import Carrera
from Cupo import Cupo
from Repositoriocupos import RepositorioCupos
from Universidad import Universidad
from Admin import Administrador

# Importar la lógica de asignación (archivo sin tilde recomendado)
from Asignación_cupos import Asignacion_cupo, SegmentQuotaStrategy, MeritStrategy

app = Flask(__name__)
app.secret_key = os.environ.get("CUPODRIVE_SECRET", "dev-secret-key")

# ---------------------------
# Estado en memoria
# ---------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

carreras_list = []       # lista de instancias Carrera
aspirantes_list = []     # lista de instancias Aspirante o dicts
uni_global = None
repo = RepositorioCupos()

# Usuarios (ejemplo)
USERS = {
    "admin": {"role": "admin", "username": "admin", "password": "admin123", "name": "Administrador"},
}

# ---------------------------
# Helpers / decoradores
# ---------------------------
def login_required(role=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            if role and session["user"].get("role") != role:
                return abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def find_cupo_by_id_global(id_cupo):
    for carrera in carreras_list:
        for cupo in getattr(carrera, "cupos", []):
            if str(getattr(cupo, "id_cupo", "")) == str(id_cupo):
                return cupo, carrera
    return None, None

def find_aspirante_by_cedula(cedula):
    """Busca en aspirantes_list una instancia (o dict) por cédula/identificación."""
    for a in aspirantes_list:
        # objeto con atributo
        try:
            if str(getattr(a, "cedula", "") or "").strip() == str(cedula).strip():
                return a
        except Exception:
            # dict con keys variadas
            if isinstance(a, dict):
                if str(a.get("identificiacion") or a.get("identificacion") or a.get("cedula") or "").strip() == str(cedula).strip():
                    return a
    return None

def find_cupo_by_aspirante(aspirante):
    """
    Busca el cupo donde cupo.aspirante == aspirante (compara por objeto o por cédula).
    Devuelve (cupo, carrera) o (None, None).
    """
    for carrera in carreras_list:
        for cup in getattr(carrera, "cupos", []):
            aspir = getattr(cup, "aspirante", None)
            if aspir is None:
                continue
            # comparaciones robustas
            try:
                if aspir is aspirante:
                    return cup, carrera
                if getattr(aspir, "cedula", None) and getattr(aspirante, "cedula", None) and str(getattr(aspir, "cedula")) == str(getattr(aspirante, "cedula")):
                    return cup, carrera
            except Exception:
                # si alguno es dict
                asp_ced = aspir.get("cedula") if isinstance(aspir, dict) else getattr(aspir, "cedula", None)
                a_ced = aspirante.get("cedula") if isinstance(aspirante, dict) else getattr(aspirante, "cedula", None)
                if asp_ced and a_ced and str(asp_ced) == str(a_ced):
                    return cup, carrera
    return None, None

# ---------------------------
# RUTAS (login)
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = USERS.get(username)
        if user and user.get("password") == password:
            session["user"] = {"username": username, "role": user["role"], "name": user.get("name", "")}
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("student_dashboard"))
        else:
            return render_template("login.html", error="Credenciales inválidas")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"ok": True})

# ---------------------------
# RUTAS ADMIN (UI)
# ---------------------------
@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    return render_template("admin.html", user=session.get("user", {}))

@app.route("/admin/upload", methods=["POST"])
@login_required(role="admin")
def admin_upload():
    """
    Subir CSVs: aspirantes (BaseDatos.csv) y carreras (Carreras.csv).
    """
    global aspirantes_list, carreras_list, uni_global

    aspir_file = request.files.get("aspirantes")
    carr_file = request.files.get("carreras")

    if not aspir_file and not carr_file:
        return jsonify({"error": "No se subió ningún archivo"}), 400

    # Guardar y cargar aspirantes
    if aspir_file:
        aspir_path = os.path.join(UPLOAD_DIR, "BaseDatos.csv")
        aspir_file.save(aspir_path)
        try:
            aspirantes_list = Cargar_datos(aspir_path).cargar()
        except Exception as e:
            return jsonify({"error": f"Error cargando aspirantes: {e}"}), 500

        # Registrar usuarios tipo student (login simple por cédula)
        for a in aspirantes_list:
            try:
                usr = getattr(a, "cedula", None) if not isinstance(a, dict) else (a.get("identificiacion") or a.get("identificacion") or a.get("cedula"))
            except Exception:
                usr = None
            if usr and str(usr) not in USERS:
                USERS[str(usr)] = {"role": "student", "username": str(usr), "password": str(usr), "name": getattr(a, "nombre", "") if not isinstance(a, dict) else (a.get("nombres") or a.get("nombre") or "")}

    # Guardar y cargar carreras
    if carr_file:
        carr_path = os.path.join(UPLOAD_DIR, "Carreras.csv")
        carr_file.save(carr_path)
        try:
            carreras_list = CargarCarreras(carr_path).cargar(as_model=True)
            # opcion: crear Universidad y agregar carreras
            try:
                uni_global = Universidad(id_universidad="102", nombre="UNIVERSIDAD (cargada)", direccion="", telefono="", correo="", estado="Activa")
                for c in carreras_list:
                    try:
                        uni_global.agregar_carrera(c)
                    except Exception:
                        pass
            except Exception:
                uni_global = None
        except Exception as e:
            return jsonify({"error": f"Error cargando carreras: {e}"}), 500

    return jsonify({"ok": True})

@app.route("/admin/assign", methods=["POST"])
@login_required(role="admin")
def admin_assign_all():
    """
    Ejecuta asignación automática para cada carrera cargada.
    """
    global carreras_list, aspirantes_list
    if not carreras_list or not aspirantes_list:
        return jsonify({"error": "No hay carreras o aspirantes cargados"}), 400

    resultados = {}
    for carrera in carreras_list:
        contexto = Asignacion_cupo(carrera, aspirantes_list, SegmentQuotaStrategy())
        asignados = contexto.asignar_cupos()
        resultados[getattr(carrera, "id_carrera", getattr(carrera, "nombre", ""))] = {
            "nombre": getattr(carrera, "nombre", ""),
            "cupos_total": getattr(carrera, "oferta_cupos", len(getattr(carrera, "cupos", []))),
            "asignados_count": len(asignados),
            "asignados": [ {"cedula": getattr(a, "cedula", "") if not isinstance(a, dict) else a.get("cedula",""), "nombre": getattr(a, "nombre", "") if not isinstance(a, dict) else (a.get("nombres") or a.get("nombre","")), "puntaje": getattr(a, "puntaje", "") if not isinstance(a, dict) else a.get("puntaje","")} for a in asignados ]
        }

    return jsonify({"ok": True, "resultados": resultados})

# ---------------------------
# API endpoints (admin)
# ---------------------------
@app.route("/api/carreras", methods=["GET"])
@login_required(role="admin")
def api_carreras():
    out = []
    for c in carreras_list:
        cid = getattr(c, "id_carrera", "") or getattr(c, "nombre", "")
        out.append({
            "id": cid,
            "nombre": getattr(c, "nombre", ""),
            "oferta_cupos": getattr(c, "oferta_cupos", len(getattr(c, "cupos", []))),
            "cupos_asignados": len([x for x in getattr(c, "cupos", []) if getattr(x, "estado", "") != "Disponible"])
        })
    return jsonify(out)

@app.route("/api/carreras/<carrera_id>/cupos", methods=["GET"])
@login_required(role="admin")
def api_carrera_cupos(carrera_id):
    for c in carreras_list:
        cid = getattr(c, "id_carrera", "") or getattr(c, "nombre", "")
        if str(cid) == str(carrera_id) or getattr(c, "nombre", "") == carrera_id:
            cupos = []
            for cup in getattr(c, "cupos", []):
                aspir = getattr(cup, "aspirante", None)
                cupos.append({
                    "id_cupo": getattr(cup, "id_cupo", ""),
                    "estado": getattr(cup, "estado", ""),
                    "aspirante": {
                        "cedula": getattr(aspir, "cedula", "") if aspir else "",
                        "nombre": getattr(aspir, "nombre", "") if aspir else ""
                    } if aspir else None
                })
            return jsonify({"carrera": getattr(c, "nombre", ""), "cupos": cupos})
    return jsonify({"error": "Carrera no encontrada"}), 404

@app.route("/api/aspirantes", methods=["GET"])
@login_required(role="admin")
def api_aspirantes():
    out = []
    for a in aspirantes_list:
        if isinstance(a, dict):
            cedula = a.get("identificiacion") or a.get("identificacion") or a.get("cedula") or a.get("ident")
            nombre = (a.get("nombres") or a.get("nombre") or "") + " " + (a.get("apellidos") or "")
            puntaje = a.get("puntaje_postulacion") or a.get("puntaje") or a.get("puntaje_post")
            estado = a.get("acepta_estado") or a.get("estado") or ""
        else:
            cedula = getattr(a, "cedula", "") or getattr(a, "identificiacion", "")
            nombre = getattr(a, "nombre", "") or (getattr(a, "nombres", "") + " " + getattr(a, "apellidos", ""))
            puntaje = getattr(a, "puntaje", "") or getattr(a, "puntaje_postulacion", "")
            estado = getattr(a, "estado", "")
        out.append({
            "cedula": str(cedula or ""),
            "nombre": (nombre or "").strip(),
            "puntaje": puntaje or "",
            "estado": estado or ""
        })
    return jsonify(out)

@app.route("/api/cupos/<id_cupo>/liberar", methods=["POST"])
@login_required(role="admin")
def api_liberar_cupo(id_cupo):
    cupo, carrera = find_cupo_by_id_global(id_cupo)
    if not cupo:
        return jsonify({"error": "Cupo no encontrado"}), 404
    try:
        # intentar método del modelo
        try:
            cupo.liberar()
        except Exception:
            # fallback: marcar disponible y quitar aspirante
            try:
                cupo.estado = "Disponible"
                cupo.aspirante = None
            except Exception:
                pass
        try:
            repo.actualizar_estado_cupo(cupo, "Disponible")
        except Exception:
            pass
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/cupos/<id_cupo>", methods=["DELETE"])
@login_required(role="admin")
def api_eliminar_cupo(id_cupo):
    cupo, carrera = find_cupo_by_id_global(id_cupo)
    if not cupo or not carrera:
        return jsonify({"error": "Cupo no encontrado"}), 404
    try:
        carrera.cupos = [c for c in carrera.cupos if str(getattr(c, "id_cupo", "")) != str(id_cupo)]
        try:
            repo.actualizar_estado_cupo(cupo, "Eliminado")
        except Exception:
            pass
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/report", methods=["POST"])
@login_required(role="admin")
def admin_report():
    admin = Administrador("000", "Sistema", "admin", "xxxx", "Administrador")
    try:
        admin.generar_reporte(aspirantes_list if aspirantes_list else [])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------
# RUTAS ESTUDIANTE
# ---------------------------
@app.route("/student")
@login_required(role="student")
def student_dashboard():
    username = session["user"]["username"]
    aspir = find_aspirante_by_cedula(username)
    # Preparar diccionario simple para template (evita atributos en plantilla)
    if aspir is None:
        aspir_data = {"cedula": username, "nombre": "", "puntaje": "", "estado": "", "carrera_asignada": ""}
    else:
        if isinstance(aspir, dict):
            nombre = (aspir.get("nombres") or aspir.get("nombre") or "").strip()
            puntaje = aspir.get("puntaje_postulacion") or aspir.get("puntaje") or ""
            estado = aspir.get("estado") or ""
        else:
            nombre = getattr(aspir, "nombre", "")
            puntaje = getattr(aspir, "puntaje", "")
            estado = getattr(aspir, "estado", "")
        # intentar encontrar carrera asignada
        cupo, carrera = find_cupo_by_aspirante(aspir)
        carrera_nombre = getattr(carrera, "nombre", "") if carrera else ""
        aspir_data = {"cedula": getattr(aspir, "cedula", "") if not isinstance(aspir, dict) else (aspir.get("identificiacion") or aspir.get("identificacion") or aspir.get("cedula")), "nombre": nombre, "puntaje": puntaje, "estado": estado, "carrera_asignada": carrera_nombre}
    return render_template("student.html", user=session.get("user", {}), aspirante=aspir_data)

@app.route("/student/cupo/accept", methods=["POST"])
@login_required(role="student")
def student_accept_cupo():
    username = session["user"]["username"]
    aspir = find_aspirante_by_cedula(username)
    if not aspir:
        return jsonify({"error": "Aspirante no encontrado"}), 404

    est = getattr(aspir, "estado", "") if not isinstance(aspir, dict) else aspir.get("estado", "")
    if str(est).lower() not in ("asignado", "asigned", "assigned", "aceptado", "aceptar"):
        if str(est).lower() == "aceptado":
            report_url = url_for("student_report", cedula=getattr(aspir, "cedula", "") or (aspir.get("cedula") if isinstance(aspir, dict) else ""), _external=False)
            return jsonify({"ok": True, "report_url": report_url})
        return jsonify({"error": "No hay un cupo asignado para aceptar"}), 400

    if isinstance(aspir, dict):
        aspir["estado"] = "Aceptado"
    else:
        aspir.estado = "Aceptado"

    cupo, carrera = find_cupo_by_aspirante(aspir)
    if cupo:
        try:
            cupo.estado = "Aceptado"
        except Exception:
            try:
                setattr(cupo, "estado", "Aceptado")
            except Exception:
                pass
        try:
            repo.actualizar_estado_cupo(cupo, "Aceptado")
        except Exception:
            pass

    cedula = getattr(aspir, "cedula", "") or (aspir.get("cedula") if isinstance(aspir, dict) else "")
    report_url = url_for("student_report", cedula=cedula)
    return jsonify({"ok": True, "report_url": report_url})

@app.route("/student/cupo/reject", methods=["POST"])
@login_required(role="student")
def student_reject_cupo():
    username = session["user"]["username"]
    aspir = find_aspirante_by_cedula(username)
    if not aspir:
        return jsonify({"error": "Aspirante no encontrado"}), 404

    est = getattr(aspir, "estado", "") if not isinstance(aspir, dict) else aspir.get("estado", "")
    if str(est).lower() not in ("asignado", "aceptado", "assigned"):
        return jsonify({"error": "No hay un cupo asignado para rechazar"}), 400

    if isinstance(aspir, dict):
        aspir["estado"] = "Rechazado"
    else:
        aspir.estado = "Rechazado"

    cupo, carrera = find_cupo_by_aspirante(aspir)
    if cupo:
        try:
            cupo.liberar()
        except Exception:
            try:
                cupo.estado = "Disponible"
                cupo.aspirante = None
            except Exception:
                pass
        try:
            repo.actualizar_estado_cupo(cupo, "Disponible")
        except Exception:
            pass

    # re-ejecutar asignación en la carrera para cubrir la vacante (intento)
    if carrera:
        try:
            contexto = Asignacion_cupo(carrera, aspirantes_list, SegmentQuotaStrategy())
            contexto.asignar_cupos()
        except Exception:
            pass

    return jsonify({"ok": True})

@app.route("/student/report/<cedula>", methods=["GET"])
@login_required(role="student")
def student_report(cedula):
    aspir = find_aspirante_by_cedula(cedula)
    if not aspir:
        return "Aspirante no encontrado", 404

    cupo, carrera = find_cupo_by_aspirante(aspir)
    carrera_nombre = getattr(carrera, "nombre", "") if carrera else (carrera.get("nombre") if isinstance(carrera, dict) else "")
    aspir_data = {
        "cedula": getattr(aspir, "cedula", "") if not isinstance(aspir, dict) else (aspir.get("identificiacion") or aspir.get("identificacion") or aspir.get("cedula")),
        "nombre": getattr(aspir, "nombre", "") if not isinstance(aspir, dict) else (aspir.get("nombres") or aspir.get("nombre") or ""),
        "puntaje": getattr(aspir, "puntaje", "") if not isinstance(aspir, dict) else (aspir.get("puntaje_postulacion") or aspir.get("puntaje") or ""),
        "estado": getattr(aspir, "estado", "") if not isinstance(aspir, dict) else (aspir.get("estado") or "")
    }
    from datetime import date
    now = date.today().isoformat()
    return render_template("report_acceptance.html", aspirante=aspir_data, carrera=carrera_nombre, now_date=now)

# ---------------------------
# Inicialización: cargar archivos por defecto si existen
# ---------------------------
def load_default_data():
    global aspirantes_list, carreras_list, uni_global
    if os.path.exists("BaseDatos.csv"):
        try:
            aspirantes_list = Cargar_datos("BaseDatos.csv").cargar()
            for a in aspirantes_list:
                try:
                    usr = getattr(a, "cedula", None) if not isinstance(a, dict) else (a.get("identificiacion") or a.get("identificacion") or a.get("cedula"))
                except Exception:
                    usr = None
                if usr and str(usr) not in USERS:
                    USERS[str(usr)] = {"role": "student", "username": str(usr), "password": str(usr), "name": getattr(a, "nombre", "") if not isinstance(a, dict) else (a.get("nombres") or a.get("nombre",""))}
            print(f"Éxito: {len(aspirantes_list)} aspirantes listos.")
        except Exception as e:
            print("Advertencia: no se pudieron cargar los aspirantes por defecto.", e)
    if os.path.exists("Carreras.csv"):
        try:
            carreras_list_local = CargarCarreras("Carreras.csv").cargar(as_model=True)
            if isinstance(carreras_list, list):
                carreras_list.extend(carreras_list_local)
            else:
                carreras_list = list(carreras_list_local)
            try:
                uni = Universidad(id_universidad="102", nombre="UNIVERSIDAD (cargada)", direccion="", telefono="", correo="", estado="Activa")
                for c in carreras_list_local:
                    try:
                        uni.agregar_carrera(c)
                    except Exception:
                        pass
                globals()['uni_global'] = uni
            except Exception:
                pass
            print(f"Éxito: {len(carreras_list_local)} carreras cargadas por defecto.")
        except Exception as e:
            print("Advertencia: no se pudieron cargar las carreras por defecto.", e)

if hasattr(app, "before_serving"):
    @app.before_serving
    def _load_on_start():
        load_default_data()
elif hasattr(app, "before_first_request"):
    @app.before_first_request
    def _load_on_first():
        load_default_data()
else:
    load_default_data()

if __name__ == "__main__":
    app.run(debug=True, port=5000)