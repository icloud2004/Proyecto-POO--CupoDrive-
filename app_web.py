# Pega todo este archivo (reemplaza app_web.py existente si quieres)
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

# Importar la lógica de asignación (asegúrate del nombre del archivo Asignacion_cupos.py)
from Asignación_cupos import Asignacion_cupo, SegmentQuotaStrategy, MeritStrategy

app = Flask(__name__)
app.secret_key = os.environ.get("CUPODRIVE_SECRET", "dev-secret-key")

# Estado en memoria
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

carreras_list = []
aspirantes_list = []
uni_global = None
repo = RepositorioCupos()

USERS = {
    "admin": {"role": "admin", "username": "admin", "password": "admin123", "name": "Administrador"},
}

# Helpers / decoradores
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
    for a in aspirantes_list:
        try:
            if str(getattr(a, "cedula", "") or "").strip() == str(cedula).strip():
                return a
        except Exception:
            if isinstance(a, dict):
                if str(a.get("identificiacion") or a.get("identificacion") or a.get("cedula") or "").strip() == str(cedula).strip():
                    return a
    return None

def find_cupo_by_aspirante(aspirante):
    for carrera in carreras_list:
        for cup in getattr(carrera, "cupos", []):
            aspir = getattr(cup, "aspirante", None)
            if aspir is None:
                continue
            try:
                if aspir is aspirante:
                    return cup, carrera
                if getattr(aspir, "cedula", None) and getattr(aspirante, "cedula", None) and str(getattr(aspir, "cedula")) == str(getattr(aspirante, "cedula")):
                    return cup, carrera
            except Exception:
                asp_ced = aspir.get("cedula") if isinstance(aspir, dict) else getattr(aspir, "cedula", None)
                a_ced = aspirante.get("cedula") if isinstance(aspirante, dict) else getattr(aspirante, "cedula", None)
                if asp_ced and a_ced and str(asp_ced) == str(a_ced):
                    return cup, carrera
    return None, None

# RUTAS (login)
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

# (Aquí estarían las rutas admin y APIs — mantenlas como en tu app, no las repito para no duplicar)

# RUTA ESTUDIANTE (usar plantilla 'estudiante.html')
@app.route("/student")
@login_required(role="student")
def student_dashboard():
    username = session["user"]["username"]
    aspir = find_aspirante_by_cedula(username)
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
        cupo, carrera = find_cupo_by_aspirante(aspir)
        carrera_nombre = getattr(carrera, "nombre", "") if carrera else ""
        ced = getattr(aspir, "cedula", "") if not isinstance(aspir, dict) else (aspir.get("identificiacion") or aspir.get("identificacion") or aspir.get("cedula"))
        aspir_data = {"cedula": ced, "nombre": nombre, "puntaje": puntaje, "estado": estado, "carrera_asignada": carrera_nombre}
    return render_template("estudiante.html", user=session.get("user", {}), aspirante=aspir_data)

# ENDPOINT: aceptar cupo
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
    # build URL that opens the reporte template route (below)
    report_url = url_for("student_report", cedula=cedula)
    return jsonify({"ok": True, "report_url": report_url})

# ENDPOINT: rechazar cupo
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

    if carrera:
        try:
            contexto = Asignacion_cupo(carrera, aspirantes_list, SegmentQuotaStrategy())
            contexto.asignar_cupos()
        except Exception:
            pass

    return jsonify({"ok": True})

# RUTA DEL REPORTE (usa plantilla 'reporte.html')
@app.route("/student/reporte/<cedula>", methods=["GET"])
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
    return render_template("reporte.html", aspirante=aspir_data, carrera=carrera_nombre, now_date=now)

# Inicialización: cargar archivos por defecto si existen (mantén tu lógica aquí)
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
            print("Advertencia:", e)
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
            print("Advertencia:", e)

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