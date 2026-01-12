# app_web.py (modificado: soporte de segmentos GLOBALES en lugar de segmentos por carrera en UI)
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
import os
import traceback
import json

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

# Importar modelos y lógica
try:
    from Carrera import Carrera
except Exception:
    Carrera = None

try:
    from Cupo import Cupo
except Exception:
    Cupo = None

try:
    from Repositoriocupos import RepositorioCupos
except Exception:
    RepositorioCupos = None

try:
    from Universidad import Universidad
except Exception:
    Universidad = None

# Importar estrategias (la asignación seguirá usando Strategy; MultiSegmentStrategy usará los segmentos globales)
try:
    from Asignación_cupos import Asignacion_cupo, MultiSegmentStrategy, SegmentQuotaStrategy, MeritStrategy, LotteryStrategy
except Exception:
    try:
        from Asignación_cupos import Asignacion_cupo, MultiSegmentStrategy, SegmentQuotaStrategy, MeritStrategy, LotteryStrategy
    except Exception:
        Asignacion_cupo = None
        MultiSegmentStrategy = None
        SegmentQuotaStrategy = None
        MeritStrategy = None
        LotteryStrategy = None

# Persistencia helpers (intentar importar)
try:
    from persistencia import save_aspirantes, load_aspirantes, save_cupos, load_cupos
except Exception:
    # shims básicos
    def save_aspirantes(*args, **kwargs):
        pass
    def load_aspirantes(*args, **kwargs):
        return []
    def save_cupos(*args, **kwargs):
        pass
    def load_cupos(*args, **kwargs):
        return []

app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(__file__), "templates")
app.secret_key = os.environ.get("CUPODRIVE_SECRET", "dev-secret-key")

# ---------------------------
# Estado en memoria & paths
# ---------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
GLOBAL_SEGMENTOS_PATH = os.path.join(DATA_DIR, "segmentos_global.json")

carreras_list = []       # lista de instancias Carrera
aspirantes_list = []     # lista de instancias Aspirante o dicts
uni_global = None
repo = None

def ensure_repo():
    global repo
    try:
        if repo is None and RepositorioCupos is not None:
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

# ---------------------------
# Utils & finders
# ---------------------------
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

# ---------------------------
# Auth decorator (simple)
# ---------------------------
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

# ---------------------------
# Routes: login / admin
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

@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    return render_template("admin.html", user=session.get("user", {}))

# ---------------------------
# Admin endpoints: upload, assign
# ---------------------------
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

        # Persistir aspirantes a JSON (persistencia puede dedupe)
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
    if Asignacion_cupo is None:
        return jsonify({"error": "Módulo de asignación no disponible"}), 500

    # Cargar segmentos globales y asignarlos a cada carrera antes de ejecutar la estrategia
    global_segments = load_global_segmentos()  # lista de dicts
    # si hay segmentos globales, aplicarlos a cada carrera (reconstruir Segmento objects)
    if global_segments:
        try:
            from Segmento import Segmento
            seg_objs = [Segmento.from_dict(s) for s in global_segments]
            for c in carreras_list:
                c.segmentos = seg_objs.copy()
        except Exception:
            pass

    resultados = {}
    # usar MultiSegmentStrategy por defecto (si está disponible) para respetar múltiples segmentos
    StrategyClass = MultiSegmentStrategy or SegmentQuotaStrategy or MeritStrategy
    for carrera in carreras_list:
        try:
            contexto = Asignacion_cupo(carrera, aspirantes_list, StrategyClass())
            asignados = contexto.asignar_cupos()
        except Exception as e:
            asignados = []
            print("Error asignando a carrera", getattr(carrera, "nombre", ""), e)

        resultados[getattr(carrera, "id_carrera", getattr(carrera, "nombre", ""))] = {
            "nombre": getattr(carrera, "nombre", ""),
            "cupos_total": getattr(carrera, "oferta_cupos", len(getattr(carrera, "cupos", []))),
            "asignados_count": len(asignados),
            "asignados": [ {"cedula": getattr(a, "cedula", "") if not isinstance(a, dict) else a.get("cedula",""), "nombre": getattr(a, "nombre", "") if not isinstance(a, dict) else (a.get("nombres") or a.get("nombre","")), "puntaje": getattr(a, "puntaje", "") if not isinstance(a, dict) else a.get("puntaje","")} for a in asignados ]
        }

    # persistir cambios en cupos
    try:
        r = ensure_repo()
        if r:
            try:
                r.save_all()
            except Exception:
                save_cupos(carreras_list)
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

@app.route("/api/carreras/<carrera_id>/cupos", methods=["DELETE"])
@login_required(role="admin")
def api_eliminar_todos_cupos(carrera_id):
    for c in carreras_list:
        cid = getattr(c, "id_carrera", "") or getattr(c, "nombre", "")
        if str(cid) == str(carrera_id) or getattr(c, "nombre", "") == carrera_id:
            try:
                removed_count = len(getattr(c, "cupos", []))
                c.cupos = []
                try:
                    c.oferta_cupos = 0
                except Exception:
                    pass
                try:
                    r = ensure_repo()
                    if r and hasattr(r, "save_all"):
                        r.save_all()
                    else:
                        save_cupos(carreras_list)
                except Exception:
                    pass
                return jsonify({"ok": True, "removed": removed_count})
            except Exception as e:
                return jsonify({"error": "Error eliminando cupos: " + str(e)}), 500
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
# Endpoints para segmentos GLOBALES
# ---------------------------
def load_global_segmentos():
    try:
        if os.path.exists(GLOBAL_SEGMENTOS_PATH):
            with open(GLOBAL_SEGMENTOS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data or []
    except Exception:
        traceback.print_exc()
    return []

def save_global_segmentos(seg_list):
    try:
        with open(GLOBAL_SEGMENTOS_PATH, "w", encoding="utf-8") as f:
            json.dump(seg_list, f, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()

@app.route("/api/segmentos", methods=["GET"])
@login_required(role="admin")
def api_get_global_segmentos():
    segs = load_global_segmentos()
    return jsonify({"ok": True, "segmentos": segs})

@app.route("/api/segmentos", methods=["POST"])
@login_required(role="admin")
def api_set_global_segmentos():
    payload = request.get_json() or {}
    segmentos_payload = payload.get("segmentos", [])
    if not isinstance(segmentos_payload, list):
        return jsonify({"error": "Payload inválido"}), 400
    suma = sum([float(s.get("porcentaje", 0) or 0) for s in segmentos_payload])
    if abs(suma - 100.0) > 0.0001:
        return jsonify({"error": f"La suma de porcentajes debe ser 100. Actualmente: {suma}"}), 400
    # normalize and persist
    normalized = []
    for s in segmentos_payload:
        normalized.append({
            "nombre": str(s.get("nombre","")).strip(),
            "porcentaje": float(s.get("porcentaje", 0) or 0),
            "orden": int(s.get("orden", 100) or 100),
            "min_pct": s.get("min_pct", None),
            "max_pct": s.get("max_pct", None),
            "descripcion": s.get("descripcion", "")
        })
    save_global_segmentos(normalized)
    return jsonify({"ok": True, "segmentos": normalized})

@app.route("/api/segmentos/<segmento_nombre>", methods=["DELETE"])
@login_required(role="admin")
def api_delete_global_segmento(segmento_nombre):
    segs = load_global_segmentos()
    new = [s for s in segs if str(s.get("nombre","")).strip().lower() != str(segmento_nombre).strip().lower()]
    if len(new) == len(segs):
        return jsonify({"error": "Segmento no encontrado"}), 404
    save_global_segmentos(new)
    return jsonify({"ok": True})

# ---------------------------
# Inicialización segura (carga predeterminada)
# ---------------------------
def load_default_data():
    global aspirantes_list, carreras_list, uni_global, repo
    try:
        aspirantes_list = []
    except Exception:
        pass
    try:
        carreras_list = []
    except Exception:
        pass

    # cargar aspirantes persistidos
    try:
        persisted_asp = load_aspirantes()
        if persisted_asp:
            aspirantes_list = list(persisted_asp)
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

    # cargar CSV aspirantes si existe (sobrescribe)
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

    # CARGA DE CARRERAS Y RECONSTRUCCIÓN DE CUPOS (respeta data/cupos.json)
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

            # cargar cupos persistidos si existe
            cupos_file_path = os.path.join(os.path.dirname(__file__), "data", "cupos.json")
            cupos_exist_file = os.path.exists(cupos_file_path)

            if cupos_exist_file:
                persisted = load_cupos()
                # agrupar por carrera_id
                from collections import defaultdict
                records_by_carrera = defaultdict(list)
                for rec in (persisted or []):
                    key = str(rec.get("carrera_id") or rec.get("carrera_nombre") or "").strip()
                    records_by_carrera[key].append(rec)
                from Cupo import Cupo as CupoClass
                for c in carreras_list:
                    cid_key = str(getattr(c, "id_carrera", "") or getattr(c, "nombre", "")).strip()
                    recs = records_by_carrera.get(cid_key) or records_by_carrera.get(getattr(c, "nombre", ""))
                    if recs is None:
                        # generar cupos si no existían y no hay persistencia
                        if not getattr(c, "cupos", None):
                            c.cupos = []
                            for i in range(1, max(0, getattr(c, "oferta_cupos", 0)) + 1):
                                try:
                                    c.cupos.append(CupoClass(id_cupo=f"{getattr(c,'id_carrera','')}-{i}", carrera=getattr(c, "nombre", "")))
                                except Exception:
                                    cup = type("SimpleCupo", (), {})()
                                    setattr(cup, "id_cupo", f"{getattr(c,'id_carrera','')}-{i}")
                                    setattr(cup, "carrera", getattr(c, "nombre", ""))
                                    setattr(cup, "estado", "Disponible")
                                    setattr(cup, "aspirante", None)
                                    c.cupos.append(cup)
                    else:
                        # if persisted is empty list => respect absence of cupos
                        if len(recs) == 0:
                            c.cupos = []
                            continue
                        recs_sorted = sorted(recs, key=lambda r: str(r.get("id_cupo", "")))
                        new_cupos = []
                        for rec in recs_sorted:
                            try:
                                cupo_obj = CupoClass(id_cupo=rec.get("id_cupo"), carrera=getattr(c, "nombre", ""))
                            except Exception:
                                cupo_obj = type("SimpleCupo", (), {})()
                                setattr(cupo_obj, "id_cupo", rec.get("id_cupo"))
                                setattr(cupo_obj, "carrera", getattr(c, "nombre", ""))
                            try:
                                setattr(cupo_obj, "estado", rec.get("estado", "") or "Disponible")
                            except Exception:
                                pass
                            aspir_ced = str(rec.get("aspirante_cedula", "") or "").strip()
                            if aspir_ced:
                                aspir_obj = find_aspirante_by_cedula(aspir_ced)
                                if aspir_obj:
                                    try:
                                        setattr(cupo_obj, "aspirante", aspir_obj)
                                    except Exception:
                                        pass
                            new_cupos.append(cupo_obj)
                        c.cupos = new_cupos

            else:
                # no existe archivo de cupos -> generar desde oferta
                for c in carreras_list:
                    try:
                        if not getattr(c, "cupos", None):
                            c.cupos = []
                            for i in range(1, max(0, getattr(c, "oferta_cupos", 0)) + 1):
                                try:
                                    c.cupos.append(Cupo(id_cupo=f"{getattr(c,'id_carrera','')}-{i}", carrera=getattr(c, "nombre", "")))
                                except Exception:
                                    cup = type("SimpleCupo", (), {})()
                                    setattr(cup, "id_cupo", f"{getattr(c,'id_carrera','')}-{i}")
                                    setattr(cup, "carrera", getattr(c, "nombre", ""))
                                    setattr(cup, "estado", "Disponible")
                                    setattr(cup, "aspirante", None)
                                    c.cupos.append(cup)
                    except Exception:
                        pass

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

            print(f"Éxito: {len(carreras_list_local)} carreras cargadas por defecto.")
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

# Ejecutar load_default_data solo en proceso correcto para evitar duplicado por reloader
def load_default_data_once():
    is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    is_flask_cli = os.environ.get("FLASK_RUN_FROM_CLI") == "true"
    if not (is_reloader_child or is_flask_cli or not app.debug):
        return
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