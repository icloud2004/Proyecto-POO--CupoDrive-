
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
import os
import traceback

# Intentar importar cargadores con varios nombres posibles (repos pueden variar)
try:
    from Cargar_datos import Cargar_datos
except Exception:
    Cargar_datos = None

try:
    from Cargar_carrera import CargarCarreras
except Exception:
    try:
        from Cargar_carrera import CargarCarreras
    except Exception:
        CargarCarreras = None

from Carrera import Carrera
from Cupo import Cupo
from Repositoriocupos import RepositorioCupos
from Universidad import Universidad
from Admin import Administrador

# Intentar importar módulo de asignación con y sin tilde
try:
    from Asignación_cupos import Asignacion_cupo, SegmentQuotaStrategy, MeritStrategy
except Exception:
    try:
        from Asignación_cupos import Asignacion_cupo, SegmentQuotaStrategy, MeritStrategy
    except Exception:
        Asignacion_cupo = None
        SegmentQuotaStrategy = None
        MeritStrategy = None

# Importar persistencia JSON (guardar/leer)
try:
    from persistencia import save_aspirantes, load_aspirantes, save_cupos, load_cupos
except Exception:
    def save_aspirantes(*args, **kwargs):
        print("persistencia.save_aspirantes no disponible")

    def load_aspirantes(*args, **kwargs):
        return []

    def save_cupos(*args, **kwargs):
        print("persistencia.save_cupos no disponible")

    def load_cupos(*args, **kwargs):
        return []

app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(__file__), "templates")
app.secret_key = os.environ.get("CUPODRIVE_SECRET", "dev-secret-key")

# ---------------------------
# Estado en memoria
# ---------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

carreras_list = []       # lista de instancias Carrera
aspirantes_list = []     # lista de instancias Aspirante o dicts
uni_global = None
repo = None

def ensure_repo():
    global repo
    try:
        if repo is None:
            repo = RepositorioCupos(carreras_list_ref=carreras_list)
        else:
            if getattr(repo, "carreras_ref", None) is None and carreras_list:
                repo.carreras_ref = carreras_list
                try:
                    if hasattr(repo, "_apply_persisted_to_carreras"):
                        repo._apply_persisted_to_carreras()
                except Exception:
                    traceback.print_exc()
    except Exception:
        traceback.print_exc()
    return repo

USERS = {
    "admin": {"role": "admin", "username": "admin", "password": "admin123", "name": "Administrador"},
}

def login_required(role=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user" not in session:
                return redirect("/login" if "login" in globals() else "/")
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
                return redirect("/admin")
            else:
                return redirect("/student")
        else:
            return render_template("login.html", error="Credenciales inválidas")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"ok": True})

# ---------------------------
# RUTAS ADMIN (resumidas; mantiene lógica existente)
# ---------------------------
@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    return render_template("admin.html", user=session.get("user", {}))

@app.route("/admin/upload", methods=["POST"])
@login_required(role="admin")
def admin_upload():
    global aspirantes_list, carreras_list, uni_global, repo

    aspir_file = request.files.get("aspirantes")
    carr_file = request.files.get("carreras")

    if not aspir_file and not carr_file:
        return jsonify({"error": "No se subió ningún archivo"}), 400

    # Guardar y cargar aspirantes
    if aspir_file:
        aspir_path = os.path.join(UPLOAD_DIR, "BaseDatos.csv")
        aspir_file.save(aspir_path)
        if Cargar_datos is None:
            return jsonify({"error": "Cargar_datos no está disponible en el servidor"}), 500
        try:
            # reemplazamos la lista actual por la lista cargada (loader evita duplicados)
            aspirantes_list = Cargar_datos(aspir_path).cargar()
        except Exception as e:
            return jsonify({"error": f"Error cargando aspirantes: {e}"}), 500

        # registrar usuarios tipo student (login simple por cédula)
        for a in aspirantes_list:
            try:
                usr = getattr(a, "cedula", None) if not isinstance(a, dict) else (a.get("identificiacion") or a.get("identificacion") or a.get("cedula"))
            except Exception:
                usr = None
            if usr and str(usr) not in USERS:
                USERS[str(usr)] = {"role": "student", "username": str(usr), "password": str(usr), "name": getattr(a, "nombre", "") if not isinstance(a, dict) else (a.get("nombres") or a.get("nombre") or "")}

        # Persistir aspirantes a JSON (persistencia hace dedupe al guardar)
        try:
            save_aspirantes(aspirantes_list)
        except Exception as e:
            print("Advertencia: no se pudo guardar aspirantes en JSON:", e)

    # Guardar y cargar carreras
    if carr_file:
        carr_path = os.path.join(UPLOAD_DIR, "Carreras.csv")
        carr_file.save(carr_path)
        if CargarCarreras is None:
            return jsonify({"error": "CargarCarreras no está disponible en el servidor"}), 500
        try:
            carreras_list = CargarCarreras(carr_path).cargar(as_model=True)
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

        try:
            repo = RepositorioCupos(carreras_list_ref=carreras_list)
            try:
                repo.save_all()
            except Exception:
                try:
                    save_cupos(carreras_list)
                except Exception:
                    pass
        except Exception as e:
            print("Advertencia: error instanciando repo tras upload:", e)

    return jsonify({"ok": True})

@app.route("/admin/assign", methods=["POST"])
@login_required(role="admin")
def admin_assign_all():
    if not carreras_list or not aspirantes_list:
        return jsonify({"error": "No hay carreras o aspirantes cargados"}), 400
    if Asignacion_cupo is None or SegmentQuotaStrategy is None:
        return jsonify({"error": "Módulo de asignación no disponible"}), 500

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

    try:
        r = ensure_repo()
        if r:
            r.save_all()
        else:
            save_cupos(carreras_list)
    except Exception as e:
        print("Advertencia: no se pudo guardar cupos tras asignación:", e)

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
            "campus": getattr(c, "campus", "") or "",
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
            nombre = (a.get("nombres") or a.get("nombre") or "").strip()
            puntaje = a.get("puntaje_postulacion") or a.get("puntaje") or a.get("puntaje_post")
            estado = a.get("acepta_estado") or a.get("estado") or ""
        else:
            cedula = getattr(a, "cedula", "") or getattr(a, "identificiacion", "")
            nombre = getattr(a, "nombre", "") or ""
            puntaje = getattr(a, "puntaje", "") or getattr(a, "puntaje_postulacion", "")
            estado = getattr(a, "estado", "")
        out.append({
            "cedula": str(cedula or ""),
            "nombre": (nombre or "").strip(),
            "puntaje": puntaje or "",
            "estado": estado or ""
        })
    return jsonify(out)

# ---------------------------
# RUTAS ESTUDIANTE (omitidas aquí; mantienen lógica previa)
# ---------------------------

# ---------------------------
# Inicialización: cargar archivos por defecto si existen (versión segura)
# ---------------------------

def load_default_data():
    """
    Carga datos persistidos (JSON) si existen; luego intenta cargar CSV si está presente.
    Se asegura de limpiar listas globales antes de poblar para evitar duplicados.
    """
    global aspirantes_list, carreras_list, uni_global, repo

    # Evitar duplicación: reiniciar las listas globales
    try:
        aspirantes_list = []
    except Exception:
        pass
    try:
        carreras_list = []
    except Exception:
        pass

    # 1) intentar cargar aspirantes persistidos (JSON)
    try:
        persisted_asp = load_aspirantes()
        if persisted_asp:
            aspirantes_list = list(persisted_asp)  # serán dicts
            for a in aspirantes_list:
                try:
                    usr = a.get("cedula") or a.get("identificacion") or a.get("identificiacion")
                except Exception:
                    usr = None
                if usr and str(usr) not in USERS:
                    USERS[str(usr)] = {"role": "student", "username": str(usr), "password": str(usr), "name": a.get("nombre", "")}
            print(f"Cargados {len(aspirantes_list)} aspirantes desde data/aspirantes.json")
    except Exception as e:
        print("Advertencia al cargar aspirantes persistidos:", e)

    # 2) Si existe BaseDatos.csv y Cargar_datos disponible, cargar CSV (opcional sobrescribir)
    if os.path.exists("BaseDatos.csv") and Cargar_datos:
        try:
            aspir_csv = Cargar_datos("BaseDatos.csv").cargar()
            if aspir_csv:
                aspirantes_list = aspir_csv
                for a in aspirantes_list:
                    try:
                        usr = getattr(a, "cedula", None) if not isinstance(a, dict) else (a.get("identificiacion") or a.get("identificacion") or a.get("cedula"))
                    except Exception:
                        usr = None
                    if usr and str(usr) not in USERS:
                        USERS[str(usr)] = {"role": "student", "username": str(usr), "password": str(usr), "name": getattr(a, "nombre", "") if not isinstance(a, dict) else (a.get("nombres") or a.get("nombre",""))}
                try:
                    save_aspirantes(aspirantes_list)
                except Exception as e:
                    print("Advertencia: no se pudo guardar aspirantes cargados desde CSV:", e)
                print(f"Éxito: {len(aspirantes_list)} aspirantes listos desde CSV.")
        except Exception as e:
            print("Advertencia: no se pudieron cargar los aspirantes desde CSV.", e)

    # 3) Cargar carreras desde CSV si existe
    if os.path.exists("Carreras.csv") and CargarCarreras:
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
            try:
                repo = RepositorioCupos(carreras_list_ref=carreras_list)
                try:
                    repo.save_all()
                except Exception:
                    try:
                        save_cupos(carreras_list)
                    except Exception:
                        pass
            except Exception as e:
                print("Advertencia: no se pudo instanciar repo al arrancar:", e)
        except Exception as e:
            print("Advertencia: no se pudieron cargar las carreras por defecto.", e)
    else:
        try:
            repo = RepositorioCupos(carreras_list_ref=carreras_list)
        except Exception:
            try:
                repo = RepositorioCupos()
            except Exception:
                repo = None

# Inicialización segura: cargar datos UNA VEZ (evita duplicados por reloader)
def load_default_data_once():
    """
    Ejecuta load_default_data sólo en el proceso correcto cuando Flask está en modo debug
    (WERKZEUG_RUN_MAIN == "true") o cuando no hay reloader.
    """
    is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    is_flask_cli = os.environ.get("FLASK_RUN_FROM_CLI") == "true"

    # cargamos si estamos en el proceso hijo del reloader (caso común con flask run)
    # o si no estamos en debug (producción) o si estamos ejecutando desde CLI
    if not (is_reloader_child or is_flask_cli or not app.debug):
        return

    # Llamamos a la función real de carga (ya limpia listas internamente)
    try:
        load_default_data()
    except Exception:
        traceback.print_exc()

if hasattr(app, "before_serving"):
    @app.before_serving
    def _load_on_start_safe():
        load_default_data_once()
elif hasattr(app, "before_first_request"):
    @app.before_first_request
    def _load_on_first_safe():
        load_default_data_once()
else:
    load_default_data_once()

if __name__ == "__main__":
    app.run(debug=True, port=5000)