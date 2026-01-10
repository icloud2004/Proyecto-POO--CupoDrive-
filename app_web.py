from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from functools import wraps
import os

# Importar clases del repo (asegúrate de que estos módulos están en el mismo directorio)
from Cargar_datos import Cargar_datos
from Carrera import Carrera
from Cupo import Cupo
from Repositoriocupos import RepositorioCupos
from Aspirante import Aspirante  # se usa para estructurar estudiantes

app = Flask(__name__)
app.secret_key = os.environ.get("CUPODRIVE_SECRET", "dev-secret-key")  # cambiar en producción

# ---------------------------
# Datos en memoria / "backend"
# ---------------------------
# Cargar aspirantes desde CSV (BaseDatos.csv)
loader = Cargar_datos("BaseDatos.csv")
aspirantes_list = loader.cargar()  # lista de objetos Aspirante

# Crear una carrera demo (puedes cargar varias si quieres)
carrera_demo = Carrera(id_carrera="001", nombre="Software", oferta_cupos=50)  # oferta por defecto 50
repo = RepositorioCupos()

# Usuarios (ejemplo): admin con credenciales y estudiantes derivados de CSV.
# En producción debes tener un sistema de usuarios real con contraseñas hashed.
USERS = {
    "admin": {"role": "admin", "username": "admin", "password": "admin123", "name": "Administrador"},
}
# Añadir estudiantes: usar su cédula como "usuario" y, por simplicidad, la cédula como password temporal.
for a in aspirantes_list:
    # usar la cédula (identificación) como username
    usr = getattr(a, "cedula", None)
    if usr:
        USERS[usr] = {"role": "student", "username": usr, "password": str(usr), "name": getattr(a, "nombre", "")}

# ---------------------------
# Helpers / decoradores
# ---------------------------
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            if role and session["user"].get("role") != role:
                return abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def find_aspirante_by_cedula(cedula):
    return next((a for a in aspirantes_list if getattr(a, "cedula", "") == cedula), None)

def find_cupo_by_id(id_cupo):
    return next((c for c in carrera_demo.cupos if str(getattr(c, 'id_cupo', '')) == str(id_cupo)), None)

# ---------------------------
# RUTAS (vistas)
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = USERS.get(username)
        if user and user.get("password") == password:
            # autenticado
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
    return jsonify({"ok": True}), 200


@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    return render_template("admin.html", user=session.get("user"))


@app.route("/student")
@login_required(role="student")
def student_dashboard():
    # estudiante se identifica por username en session (que es su cédula)
    username = session["user"]["username"]
    aspirante = find_aspirante_by_cedula(username)
    return render_template("estudiante.html", user=session.get("user"), aspirante=aspirante)

# ---------------------------
# API endpoints (JSON)
# ---------------------------
@app.route("/api/applicants", methods=["GET"])
@login_required(role="admin")
def api_applicants():
    # devolver lista de aspirantes (serializar campos relevantes)
    data = []
    for a in aspirantes_list:
        data.append({
            "cedula": getattr(a, "cedula", ""),
            "nombre": getattr(a, "nombre", ""),
            "puntaje": getattr(a, "puntaje", 0),
            "estado": getattr(a, "estado", ""),
            "vulnerabilidad": getattr(a, "vulnerabilidad", ""),
            "carrera_asignada": getattr(a, "carrera_asignada", ""),
        })
    return jsonify(data)


@app.route("/api/cupos", methods=["GET"])
@login_required(role="admin")
def api_cupos_list():
    # Lista cupos para la carrera_demo
    cups = []
    for c in carrera_demo.cupos:
        aspir = c.aspirante
        cups.append({
            "id_cupo": getattr(c, "id_cupo", ""),
            "carrera": getattr(c, "carrera", ""),
            "estado": getattr(c, "estado", ""),
            "aspirante": getattr(aspir, "nombre", "") if aspir else None,
            "aspirante_cedula": getattr(aspir, "cedula", "") if aspir else None,
            "segmento": getattr(c, "segmento", None),
        })
    return jsonify(cups)


@app.route("/api/cupos", methods=["POST"])
@login_required(role="admin")
def api_cupos_create():
    # Crear N cupos adicionales o uno nuevo con id específico
    data = request.json or {}
    cantidad = int(data.get("cantidad", 1))
    # crear cupos con ids incrementales
    start = len(carrera_demo.cupos) + 1
    for i in range(cantidad):
        cid = f"{carrera_demo.id_carrera}-{start + i}"
        carrera_demo.cupos.append(Cupo(id_cupo=cid, carrera=carrera_demo.nombre))
    return jsonify({"ok": True, "total_cupos": len(carrera_demo.cupos)}), 201


@app.route("/api/cupos/<id_cupo>", methods=["DELETE"])
@login_required(role="admin")
def api_cupos_delete(id_cupo):
    # eliminar cupo (si existe) y devolver nuevo total
    before = len(carrera_demo.cupos)
    carrera_demo.cupos = [c for c in carrera_demo.cupos if str(c.id_cupo) != str(id_cupo)]
    after = len(carrera_demo.cupos)
    return jsonify({"ok": True, "removed": before - after, "total_cupos": after}), 200


@app.route("/api/aspirante/<cedula>", methods=["GET"])
@login_required()
def api_aspirante(cedula):
    # admin o student pueden consultar; si student, solo su propia cedula permitida
    if session["user"]["role"] == "student" and session["user"]["username"] != cedula:
        return abort(403)
    a = find_aspirante_by_cedula(cedula)
    if not a:
        return jsonify({"error": "No encontrado"}), 404
    return jsonify({
        "cedula": getattr(a, "cedula", ""),
        "nombre": getattr(a, "nombre", ""),
        "puntaje": getattr(a, "puntaje", 0),
        "estado": getattr(a, "estado", ""),
        "carrera_asignada": getattr(a, "carrera_asignada", ""),
        "vulnerabilidad": getattr(a, "vulnerabilidad", ""),
        "fecha_inscripcion": getattr(a, "fecha_inscripcion", "")
    })


@app.route("/api/aceptar", methods=["POST"])
@login_required(role="student")
def api_aceptar():
    # El estudiante en sesión acepta su cupo
    username = session["user"]["username"]
    aspirante = find_aspirante_by_cedula(username)
    if not aspirante:
        return jsonify({"error": "No encontrado"}), 404
    # buscar cupo asignado al aspirante
    cupo = next((c for c in carrera_demo.cupos if getattr(c, "aspirante", None) is aspirante), None)
    if not cupo or getattr(aspirante, "estado", "") != "Asignado":
        return jsonify({"error": "No tiene cupo asignado"}), 400
    # cambios de estado usando métodos de tus clases
    try:
        cupo.aceptar()
    except Exception:
        cupo.estado = "Aceptado"
    try:
        aspirante.aceptar_cupo(cupo)
    except Exception:
        aspirante.estado = "Aceptado"
        aspirante.carrera_asignada = cupo.carrera
    repo.registrar_aceptacion(aspirante, cupo, "GUI")
    return jsonify({"ok": True}), 200


# ADMIN ACTION: asignar un cupo específico a un aspirante
@app.route("/api/assign", methods=["POST"])
@login_required(role="admin")
def api_assign():
    data = request.json or {}
    id_cupo = data.get("id_cupo")
    cedula = data.get("cedula")
    if not id_cupo or not cedula:
        return jsonify({"error": "id_cupo y cedula son requeridos"}), 400

    cupo = find_cupo_by_id(id_cupo)
    if not cupo:
        return jsonify({"error": "Cupo no encontrado"}), 404
    aspirante = find_aspirante_by_cedula(cedula)
    if not aspirante:
        return jsonify({"error": "Aspirante no encontrado"}), 404

    if getattr(cupo, "estado", "") != "Disponible":
        return jsonify({"error": "El cupo no está disponible"}), 400

    try:
        cupo.asignar_aspirante(aspirante)
    except Exception:
        cupo.aspirante = aspirante
        cupo.estado = "Asignado"

    aspirante.carrera_asignada = carrera_demo.nombre
    aspirante.estado = "Asignado"

    repo.actualizar_estado_aspirante(aspirante, "Asignado")
    repo.actualizar_estado_cupo(cupo, "Asignado")

    return jsonify({"ok": True, "message": f"Cupo {cupo.id_cupo} asignado a {aspirante.nombre}"}), 200


# ADMIN ACTION: liberar un cupo
@app.route("/api/liberar", methods=["POST"])
@login_required(role="admin")
def api_liberar():
    data = request.json or {}
    id_cupo = data.get("id_cupo")
    if not id_cupo:
        return jsonify({"error": "id_cupo es requerido"}), 400
    cupo = find_cupo_by_id(id_cupo)
    if not cupo:
        return jsonify({"error": "Cupo no encontrado"}), 404

    try:
        cupo.liberar()
    except Exception:
        cupo.aspirante = None
        cupo.estado = "Disponible"

    repo.actualizar_estado_cupo(cupo, "Disponible")
    return jsonify({"ok": True, "message": f"Cupo {id_cupo} liberado"}), 200


# ADMIN ACTION: asignación automática por mérito
@app.route("/api/assign_auto", methods=["POST"])
@login_required(role="admin")
def api_assign_auto():
    # obtener postulados
    postulados = [a for a in aspirantes_list if getattr(a, "estado", "") == "Postulado"]
    postulados = sorted(postulados, key=lambda x: getattr(x, "puntaje", 0), reverse=True)
    cupos_disponibles = carrera_demo.obtener_cupos_disponibles()

    asignados = []
    for i in range(min(len(cupos_disponibles), len(postulados))):
        aspirante = postulados[i]
        cupo = cupos_disponibles[i]
        try:
            cupo.asignar_aspirante(aspirante)
        except Exception:
            cupo.aspirante = aspirante
            cupo.estado = "Asignado"
        aspirante.carrera_asignada = carrera_demo.nombre
        aspirante.estado = "Asignado"
        repo.actualizar_estado_aspirante(aspirante, "Asignado")
        repo.actualizar_estado_cupo(cupo, "Asignado")
        asignados.append({"cupo": getattr(cupo, 'id_cupo', ''), "cedula": getattr(aspirante, 'cedula', ''), "nombre": getattr(aspirante, 'nombre', '')})

    return jsonify({"ok": True, "assigned": asignados}), 200


# ---------------------------
# Ejecutar
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
