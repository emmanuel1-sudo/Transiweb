import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename
from flask import Blueprint, request, session, redirect
import bcrypt
from MVC.models.config.database import conectar_bd



auth = Blueprint("auth", __name__)

@auth.route("/enviar_documentacion", methods=["POST"])
def enviar_documentacion():

    if "usuario_id" not in session:
        return redirect("/login.html")

    tramite = request.form.get("tramite", "").strip()
    archivos = request.files.getlist("documentos")

    if not tramite or not archivos or archivos[0].filename == "":
        return "Debes seleccionar el trámite y adjuntar los PDF.", 400

    # Carpeta para guardar los documentos
    carpeta = os.path.join(
        current_app.root_path,
        "documentos_tramites"
    )

    os.makedirs(carpeta, exist_ok=True)

    for archivo in archivos:

        if not archivo.filename.lower().endswith(".pdf"):
            return "Solo se permiten archivos PDF.", 400

        nombre_seguro = secure_filename(archivo.filename)

        # Nombre único para evitar sobrescribir archivos
        nombre_archivo = f"{uuid.uuid4().hex}_{nombre_seguro}"

        ruta_archivo = os.path.join(carpeta, nombre_archivo)

        archivo.save(ruta_archivo)

    return """
        <h2>¡Documentación enviada!</h2>
        <p>Tus documentos fueron recibidos correctamente.</p>
        <a href="/panel_usuario">Volver al panel</a>
    """


@auth.route("/login", methods=["POST"])
def login():
    correo = request.form.get("correo", "").strip()
    password = request.form.get("password", "")

    if not correo or not password:
        return "Debes ingresar el correo y la contraseña.", 400

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, nombre, correo, password, rol
            FROM usuarios
            WHERE correo = %s
            LIMIT 1
            """,
            (correo,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            return redirect("/login.html?error=credenciales")
        
        hash_guardado = usuario["password"]

        if isinstance(hash_guardado, str):
            hash_guardado = hash_guardado.encode("utf-8")

        if hash_guardado.startswith(b"$2y$"):
            hash_guardado = b"$2b$" + hash_guardado[4:]

        try:
            contraseña_valida = bcrypt.checkpw(
                password.encode("utf-8"),
                hash_guardado
            )
        except (ValueError, TypeError):
            contraseña_valida = False

        if not contraseña_valida:
            return redirect("/login.html?error=credenciales")

        session.clear()
        session["usuario_id"] = usuario["id"]
        session["usuario_nombre"] = usuario["nombre"]
        session["usuario_correo"] = usuario["correo"]

        rol = (usuario["rol"] or "").strip().lower()
        session["usuario_rol"] = rol

        if rol in ("admin", "administrador"):
            return redirect("/admin_lobby")

        return redirect("/panel_usuario")

    except Exception:
        auth.logger.exception("Error durante el inicio de sesión")
        return "Ocurrió un error al iniciar sesión.", 500

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()
@auth.route("/registro", methods=["POST"])
def registro():
    nombre = request.form.get("nombre", "").strip()
    correo = request.form.get("correo", "").strip()
    identificacion = request.form.get("identificacion", "").strip()
    password = request.form.get("password", "")

    # Validar que todos los campos estén llenos
    if not nombre or not correo or not identificacion or not password:
        return "Todos los campos son obligatorios. <a href='/registro.html'>Volver</a>", 400

    # Validar formato básico del correo
    if "@" not in correo or "." not in correo.split("@")[-1]:
        return "El correo electrónico no es válido. <a href='/registro.html'>Volver</a>", 400

    # Encriptar la contraseña usando bcrypt
    password_segura = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        # Insertar el nuevo usuario
        cursor.execute(
            """
            INSERT INTO usuarios
            (nombre, correo, identificacion, password)
            VALUES (%s, %s, %s, %s)
            """,
            (nombre, correo, identificacion, password_segura)
        )

        conexion.commit()

        return """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Registro exitoso - Transiweb</title>
            <link rel="stylesheet" href="/vista/style/styles.css">
        </head>
        <body>
            <main class="mensaje-registro">
                <div class="tarjeta-mensaje">
                    <div class="icono-exito">&#10003;</div>

                    <h2>¡Cuenta creada!</h2>

                    <p>
                        Tu cuenta de Transiweb se creó correctamente.
                        Ya puedes iniciar sesión.
                    </p>

                    <a href="/login.html" class="btn-primary">
                        Iniciar sesión
                    </a>
                </div>
            </main>
        </body>
        </html>
        """

    except Exception as error:
        if conexion is not None:
            conexion.rollback()

        # Error 1062: correo o identificación duplicados
        if getattr(error, "errno", None) == 1062:
            return """
            <div class="tarjeta-mensaje">
                <h2>Usuario ya registrado</h2>
                <p>El correo o la identificación ya existen.</p>
                <a href="/registro.html" class="btn-primary">
                    Volver al registro
                </a>
            </div>
            """, 409

        auth.logger.exception("Error durante el registro")
        return "No se pudo registrar la cuenta. Verifica la tabla usuarios.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()
        
@auth.route("/cerrar_sesion")
def cerrar_sesion():
    session.clear()
    return redirect("/login.html")