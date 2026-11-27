import os
import re
import uuid
import bcrypt

from dotenv import load_dotenv
from flask import (
    Flask,
    send_from_directory,
    redirect,
    session,
    render_template_string,
    request
)
from werkzeug.utils import secure_filename
from mysql.connector import IntegrityError

# ==========================================================
# CONFIGURACIÓN INICIAL
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))

from MVC.models.config.database import conectar_bd
from MVC.models.auth import auth
from MVC.admin_routes import admin_bp

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "MVC", "vista"),
    static_url_path="/vista"
)

app.config["SECRET_KEY"] = os.getenv("TRANSIWEB_SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "TRANSIWEB_SECRET_KEY needs to be configured"
    )

print("Clave secreta cargada:", bool(app.config["SECRET_KEY"]))

# Registrar los blueprints.
app.register_blueprint(admin_bp)
app.register_blueprint(auth)


# ==========================================================
# PÁGINA DE INICIO Y LOGIN
# ==========================================================

@app.route("/")
def inicio():
    return send_from_directory(
        os.path.join(BASE_DIR, "MVC", "models"),
        "index.html"
    )


@app.route("/inicio")
def pagina_principal():
    return send_from_directory(
        os.path.join(BASE_DIR, "MVC", "models"),
        "index.html"
    )


@app.route("/login.html")
def pagina_login():
    return send_from_directory(
        os.path.join(BASE_DIR, "MVC", "models"),
        "login.html"
    )


@app.route("/prueba-bd")
def prueba_bd():
    conexion = None

    try:
        conexion = conectar_bd()
        return "¡Transiweb está conectado a MySQL!"

    except Exception:
        app.logger.exception("Error al conectar con MySQL")
        return "Error de conexión con la base de datos.", 500

    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


# ==========================================================
# PANEL PRINCIPAL DEL ADMINISTRADOR
# ==========================================================

def exigir_admin():
    if not session.get("usuario_id"):
        return redirect("/login.html")

    if session.get("usuario_rol") not in ("admin", "administrador"):
        return "No tienes permisos para acceder.", 403

    return None


@app.route("/admin_lobby")
def admin_lobby():
    respuesta = exigir_admin()

    if respuesta:
        return respuesta

    ruta_html = os.path.join(
        BASE_DIR,
        "MVC",
        "models",
        "admin_lobby.html"
    )

    try:
        with open(ruta_html, "r", encoding="utf-8") as archivo:
            html = archivo.read()

        from markupsafe import escape

        nombre = escape(
            str(session.get("usuario_nombre", "Administrador"))
        )

        html = html.replace(
            '<span id="nombre-admin">Administrador</span>',
            f'<span id="nombre-admin">{nombre}</span>'
        )

        return html

    except FileNotFoundError:
        app.logger.exception("No se encontró admin_lobby.html")
        return "No se encontró admin_lobby.html.", 500


# ==========================================================
# CERRAR SESIÓN
# ==========================================================

@app.route("/logout")
def cerrar_sesion():
    session.clear()
    return redirect("/login.html")


# ==========================================================
# REGISTRO
# ==========================================================

@app.route("/registro")
def pagina_registro():
    return send_from_directory(
        os.path.join(BASE_DIR, "MVC", "models"),
        "registro.html"
    )


@app.route("/registrar", methods=["POST"])
def registrar_usuario():

    nombre = request.form.get("nombre", "").strip()
    correo = request.form.get("correo", "").strip()
    identificacion = request.form.get(
        "identificacion", ""
    ).strip()
    password = request.form.get("password", "")

    if not nombre or not correo or not identificacion or not password:
        return "Todos los campos son obligatorios.", 400

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        return "El correo electrónico no es válido.", 400

    if len(password.encode("utf-8")) > 72:
        return "La contraseña no puede superar los 72 bytes.", 400

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO usuarios
            (nombre, correo, identificacion, password)
            VALUES (%s, %s, %s, %s)
            """,
            (nombre, correo, identificacion, password_hash)
        )

        conexion.commit()

        return redirect("/login.html?registro=exitoso")

    except IntegrityError:
        if conexion:
            conexion.rollback()

        return (
            "El correo o la identificación ya están registrados.",
            409
        )

    except Exception:
        if conexion:
            conexion.rollback()

        app.logger.exception("Error al registrar usuario")

        return (
            "No se pudo crear la cuenta. Intenta nuevamente.",
            500
        )

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ==========================================================
# ARCHIVOS DE CONTROL
# ==========================================================

@app.route("/control/<path:filename>")
def archivos_control(filename):
    carpeta_control = os.path.join(
        BASE_DIR,
        "MVC",
        "control"
    )

    return send_from_directory(carpeta_control, filename)


# ==========================================================
# PANEL DEL CIUDADANO
# ==========================================================

@app.route("/panel_usuario")
def panel_usuario():

    if "usuario_id" not in session:
        return redirect("/login.html")

    if session.get("usuario_rol") in ("admin", "administrador"):
        return redirect("/admin_lobby")

    ruta = os.path.join(
        BASE_DIR,
        "MVC",
        "models",
        "lobby.html"
    )

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.read()

        return render_template_string(contenido)

    except FileNotFoundError:
        app.logger.exception("No se encontró lobby.html")
        return "No se encontró lobby.html.", 500


# ==========================================================
# CONSULTAR TRÁMITES
# ==========================================================

@app.route("/consultar_tramites")
def consultar_tramites():

    if "usuario_id" not in session:
        return redirect("/login.html")

    return send_from_directory(
        os.path.join(BASE_DIR, "MVC", "models"),
        "consultar_tramites.html"
    )


# ==========================================================
# CÓMO FUNCIONA
# ==========================================================

@app.route("/como_funciona")
def como_funciona():

    if "usuario_id" not in session:
        return redirect("/login.html")

    return send_from_directory(
        os.path.join(BASE_DIR, "MVC", "models"),
        "como_funciona.html"
    )


# ==========================================================
# SOLICITAR TRÁMITES
# ==========================================================

@app.route("/solicitar_tramite")
def solicitar_tramite():

    if "usuario_id" not in session:
        return redirect("/login.html")

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nombre, descripcion
            FROM tramites
            WHERE estado = 'activo'
            ORDER BY nombre ASC
        """)

        tramites = cursor.fetchall()

        ruta_html = os.path.join(
            BASE_DIR,
            "MVC",
            "models",
            "solicitar_tramite.html"
        )

        with open(ruta_html, "r", encoding="utf-8") as archivo:
            html = archivo.read()

        return render_template_string(
            html,
            tramites=tramites
        )

    except Exception:
        app.logger.exception("Error al cargar los trámites")
        return "No se pudieron cargar los trámites.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ==========================================================
# ENVIAR DOCUMENTACIÓN Y REGISTRAR SOLICITUD
# ==========================================================

@app.route("/enviar_documentacion", methods=["POST"])
def enviar_documentacion():

    print(
        "ENTRÓ A LA RUTA ENVIAR DOCUMENTACIÓN",
        flush=True
    )

    if "usuario_id" not in session:
        return redirect("/login.html")

    tramite_id = request.form.get("tramite_id", type=int)

    archivos = [
        archivo
        for archivo in request.files.getlist("documentos")
        if archivo and archivo.filename
    ]

    app.logger.warning("ID TRÁMITE: %s", tramite_id)
    app.logger.warning("ARCHIVOS RECIBIDOS: %s", len(archivos))
    app.logger.warning(
        "NOMBRES: %s",
        [archivo.filename for archivo in archivos]
    )

    if not tramite_id:
        return "Debes seleccionar un trámite.", 400

    if not archivos:
        return "Debes adjuntar al menos un documento PDF.", 400

    if len(archivos) > 20:
        return "Solo puedes adjuntar hasta 20 documentos.", 400

    # Validar que los archivos sean PDF.
    for archivo in archivos:

        if not archivo.filename.lower().endswith(".pdf"):
            return "Solo se permiten documentos PDF.", 400

        firma = archivo.read(5)
        archivo.seek(0)

        if firma != b"%PDF-":
            return "Uno de los archivos no es un PDF válido.", 400

    conexion = None
    cursor = None
    archivos_guardados = []

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        # Verificar que el trámite exista y esté activo.
        cursor.execute("""
            SELECT id
            FROM tramites
            WHERE id = %s AND estado = 'activo'
        """, (tramite_id,))

        tramite = cursor.fetchone()

        if not tramite:
            return "El trámite no existe o está inactivo.", 400

        # Registrar la solicitud.
        cursor.execute("""
            INSERT INTO solicitudes
            (usuario_id, tramite_id, estado)
            VALUES (%s, %s, 'pendiente')
        """, (
            session["usuario_id"],
            tramite_id
        ))

        solicitud_id = cursor.lastrowid

        # Crear carpeta para guardar los PDF.
        carpeta = os.path.join(
            BASE_DIR,
            "uploads",
            "solicitudes"
        )

        os.makedirs(carpeta, exist_ok=True)

        # Guardar cada documento.
        for archivo in archivos:

            nombre_original = secure_filename(
                archivo.filename
            )

            if not nombre_original:
                raise ValueError(
                    "Nombre de archivo no válido."
                )

            nombre_guardado = (
                uuid.uuid4().hex + "_" + nombre_original
            )

            ruta_completa = os.path.join(
                carpeta,
                nombre_guardado
            )

            ruta_relativa = os.path.join(
                "uploads",
                "solicitudes",
                nombre_guardado
            ).replace("\\", "/")

            archivo.save(ruta_completa)

            archivos_guardados.append(ruta_completa)

            cursor.execute("""
                INSERT INTO documentos_solicitud
                (solicitud_id, nombre_archivo, ruta_archivo)
                VALUES (%s, %s, %s)
            """, (
                solicitud_id,
                nombre_original,
                ruta_relativa
            ))

        conexion.commit()

        return redirect(
            "/solicitar_tramite?enviado=1"
        )

    except Exception:
        if conexion is not None:
            conexion.rollback()

        # Eliminar archivos si ocurrió un error.
        for ruta in archivos_guardados:
            if os.path.exists(ruta):
                os.remove(ruta)

        app.logger.exception(
            "Error al enviar documentación"
        )

        return "No se pudo registrar la solicitud.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()



if __name__ == "__main__":

    print("====================================")
    print("TRANSIWEB - ARCHIVO APP.PY EJECUTADO")
    print("RUTA:", os.path.abspath(__file__))
    print("====================================", flush=True)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
