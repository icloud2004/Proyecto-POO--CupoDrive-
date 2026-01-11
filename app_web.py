from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, send_file
from functools import wraps
import os
import io

# Importar clases del repo
from Cargar_datos import Cargar_datos
from Cargar_carrera import CargarCarreras
from Carrera import Carrera
from Cupo import Cupo
from Repositoriocupos import RepositorioCupos
from Universidad import Universidad
from Admin import Administrador

# Importar la lógica de asignación (asegúrate de que el archivo se llame Asignacion_cupos.py sin acento)
from Asignación_cupos import Asignacion_cupo, SegmentQuotaStrategy, MeritStrategy

app = Flask(__name__)
app.secret_key = os.environ.get("CUPODRIVE_SECRET", "dev-secret-key")  # cambiar en producción

# ---------------------------
# Estado en memoria
# ---------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Variables en memoria que el admin podrá actualizar con uploads
carreras_list = []       # lista de instancias Carrera
aspirantes_list = []     # lista de instancias Aspirante (o dicts según Cargar_datos)
uni_global = None        # instancia Universidad si la quieres usar
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
    """Busca un cupo por id en todas las carreras cargadas."""
    for carrera in carreras_list:
        for cupo in getattr(carrera, "cupos", []):
            if str(getattr(cupo, "id_cupo", "")) == str(id_cupo):
                return cupo, carrera
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

# Endpoint para subir CSVs (aspirantes y carreras)
@app.route("/admin/upload", methods=["POST"])
@login_required(role="admin")
def admin_upload():
    """
    Espera multipart form-data con campos:
    - aspirantes: archivo CSV (BaseDatos.csv)
    - carreras: archivo CSV (Carreras.csv)
    Guarda en uploads/ y carga en memoria usando Cargar_datos y Cargar_carreras.
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

        # Añadir a USERS (para login rápido por cédula)
        for a in aspirantes_list:
            usr = getattr(a, "cedula", None) or getattr(a, "identificiacion", None)
            if usr and str(usr) not in USERS:
                USERS[str(usr)] = {"role": "student", "username": str(usr), "password": str(usr), "name": getattr(a, "nombre", "")}

    # Guardar y cargar carreras
    if carr_file:
        carr_path = os.path.join(UPLOAD_DIR, "Carreras.csv")
        carr_file.save(carr_path)
        try:
            # Intenta cargar instancias Carrera si Cargar_carreras lo permite
            carreras_list = CargarCarreras(carr_path).cargar(as_model=True)
            # Si quisieras, puedes crear una Universidad para guardar periodos/carreras
            uni_global = Universidad(id_universidad="102", nombre="UNIVERSIDAD (cargada)", direccion="", telefono="", correo="", estado="Activa")
            for c in carreras_list:
                try:
                    uni_global.agregar_carrera(c)
                except Exception:
                    pass
        except Exception as e:
            return jsonify({"error": f"Error cargando carreras: {e}"}), 500

    return jsonify({"ok": True})

# Endpoint para lanzar asignación automática para todas las carreras
@app.route("/admin/assign", methods=["POST"])
@login_required(role="admin")
def admin_assign_all():
    """
    Ejecuta asignación automática para cada carrera cargada.
    - Usa SegmentQuotaStrategy por defecto (respeta segmentos y política de cuotas).
    - Modifica estados de aspirantes y cupos en memoria.
    """
    global carreras_list, aspirantes_list
    if not carreras_list or not aspirantes_list:
        return jsonify({"error": "No hay carreras o aspirantes cargados"}), 400

    resultados = {}
    for carrera in carreras_list:
        # crear contexto de asignación
        contexto = Asignacion_cupo(carrera, aspirantes_list, SegmentQuotaStrategy())
        asignados = contexto.asignar_cupos()
        # guardamos info mínima para la UI
        resultados[getattr(carrera, "id_carrera", getattr(carrera, "nombre", ""))] = {
            "nombre": getattr(carrera, "nombre", ""),
            "cupos_total": getattr(carrera, "oferta_cupos", len(getattr(carrera, "cupos", []))),
            "asignados_count": len(asignados),
            "asignados": [ {"cedula": getattr(a, "cedula", ""), "nombre": getattr(a, "nombre", ""), "puntaje": getattr(a, "puntaje", "")} for a in asignados ]
        }

    return jsonify({"ok": True, "resultados": resultados})

# API: listar carreras
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

# API: obtener cupos de una carrera
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

# API: liberar un cupo por id
@app.route("/api/cupos/<id_cupo>/liberar", methods=["POST"])
@login_required(role="admin")
def api_liberar_cupo(id_cupo):
    cupo, carrera = find_cupo_by_id_global(id_cupo)
    if not cupo:
        return jsonify({"error": "Cupo no encontrado"}), 404
    try:
        cupo.liberar()
        repo.actualizar_estado_cupo(cupo, "Disponible")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API: eliminar un cupo (lo quita de la lista)
@app.route("/api/cupos/<id_cupo>", methods=["DELETE"])
@login_required(role="admin")
def api_eliminar_cupo(id_cupo):
    cupo, carrera = find_cupo_by_id_global(id_cupo)
    if not cupo or not carrera:
        return jsonify({"error": "Cupo no encontrado"}), 404
    try:
        carrera.cupos = [c for c in carrera.cupos if str(getattr(c, "id_cupo", "")) != str(id_cupo)]
        repo.actualizar_estado_cupo(cupo, "Eliminado")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint para generar reporte usando Administrador.generar_reporte
@app.route("/admin/report", methods=["POST"])
@login_required(role="admin")
def admin_report():
    # Creamos un administrador de ejemplo (puedes ajustar los datos)
    admin = Administrador("000", "Sistema", "admin", "xxxx", "Administrador")
    try:
        # Generar reporte: la implementación actual imprime en consola.
        # Para devolverlo a la UI vamos a capturar stdout si fuera necesario (aquí retornamos ok)
        admin.generar_reporte(aspirantes_list if aspirantes_list else [])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------
# RUTAS ESTUDIANTE (simplificadas)
# ---------------------------
@app.route("/student")
@login_required(role="student")
def student_dashboard():
    username = session["user"]["username"]
    aspir = next((a for a in aspirantes_list if getattr(a, "cedula", "") == username), None)
    return render_template("estudiante.html", user=session.get("user", {}), aspirante=aspir)

# ---------------------------
# Inicialización: cargar archivos por defecto si existen
# --------------------------
# Register data loader in a way compatible con varias versiones de Flask
def load_default_data():
    global aspirantes_list, carreras_list, uni_global
    # Intentamos cargar BaseDatos.csv y Carreras.csv si existen en el repo
    if os.path.exists("BaseDatos.csv"):
        try:
            aspirantes_list = Cargar_datos("BaseDatos.csv").cargar()
            for a in aspirantes_list:
                usr = getattr(a, "cedula", None)
                if usr and str(usr) not in USERS:
                    USERS[str(usr)] = {"role": "student", "username": str(usr), "password": str(usr), "name": getattr(a, "nombre", "")}
            print(f"Éxito: {len(aspirantes_list)} aspirantes listos.")
        except Exception:
            print("Advertencia: no se pudieron cargar los aspirantes por defecto.")
    if os.path.exists("Carreras.csv"):
        try:
            carreras_list_local = CargarCarreras("Carreras.csv").cargar(as_model=True)
            carreras_list.extend(carreras_list_local)
            uni_global_local = Universidad(id_universidad="102", nombre="UNIVERSIDAD (cargada)", direccion="", telefono="", correo="", estado="Activa")
            # intentar agregar carreras a uni_global si se desea
            try:
                for c in carreras_list_local:
                    try:
                        uni_global_local.agregar_carrera(c)
                    except Exception:
                        pass
                # mantener referencia global si queremos usarla
                globals()['uni_global'] = uni_global_local
            except Exception:
                pass
            print(f"Éxito: {len(carreras_list_local)} carreras cargadas por defecto.")
        except Exception:
            print("Advertencia: no se pudieron cargar las carreras por defecto.")

# Intentamos registrar la carga automática usando before_serving o before_first_request según la versión de Flask.
if hasattr(app, "before_serving"):
    # Flask >= 2.0/2.3: antes de servir peticiones (asíncrono permitido)
    @app.before_serving
    async def _load_on_start():
        load_default_data()
elif hasattr(app, "before_first_request"):
    # Versiones antiguas de Flask
    @app.before_first_request
    def _load_on_first():
        load_default_data()
else:
    # Fallback: llamar ahora (útil si el framework no expone esos decoradores)
    load_default_data()

if __name__ == "__main__":
    app.run(debug=True, port=5000)