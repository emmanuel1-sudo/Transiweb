import os
import uuid
import hashlib
import secrets
import smtplib
import ssl

from pathlib import Path
from dotenv import load_dotenv
from flask import Blueprint, request, session, redirect, render_template_string
from datetime import datetime, timedelta
from email.message import EmailMessage
from flask import current_app
from werkzeug.utils import secure_filename
from flask import Blueprint, request, session, redirect
import bcrypt
from MVC.models.config.database import conectar_bd

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=True)

auth = Blueprint("auth", __name__)




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
        current_app.logger.exception("Error durante el inicio de sesión")
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

        current_app.logger.exception("Error durante el registro")
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


def _enviar_correo_recuperacion(destinatario, enlace):

    correo_emisor = os.environ.get("TRANSIWEB_EMAIL")
    clave_emisor = os.environ.get("TRANSIWEB_EMAIL_PASSWORD")

    print("Correo emisor:", correo_emisor)
    print("Contraseña cargada:", bool(clave_emisor))
    print("Longitud contraseña:", len(clave_emisor or ""))

    print("Correo configurado:", bool(correo_emisor))
    print("¿Contraseña configurada?:", bool(clave_emisor))
    print("Longitud contraseña:", len(clave_emisor) if clave_emisor else 0)
    print("Correo emisor configurado:", repr(correo_emisor))

    if not correo_emisor or not clave_emisor:
        raise RuntimeError(
            "Faltan las variables de configuración de Gmail."
        )

    mensaje = EmailMessage()

    mensaje["Subject"] = "Recuperación de contraseña - Transiweb"
    mensaje["From"] = correo_emisor
    mensaje["To"] = destinatario

    mensaje.set_content(
        f"""
Hola,

Recibimos una solicitud para restablecer tu contraseña de Transiweb.

Para crear una nueva contraseña, ingresa al siguiente enlace:

{enlace}

Este enlace expirará en 30 minutos.

Si no solicitaste este cambio, puedes ignorar este correo.

Equipo Transiweb
"""
    )

    contexto_ssl = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        timeout=30,
        context=contexto_ssl,
    ) as servidor:

        servidor.login(
            correo_emisor,
            clave_emisor,
        )
        servidor.send_message(mensaje)

    print("Correo de recuperación enviado correctamente.")


@auth.route("/recuperar_password", methods=["GET", "POST"])
def recuperar_password():

    if request.method == "GET":
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Recuperar contraseña | Transiweb</title>

            <style>
                * {
                    box-sizing: border-box;
                }

                body {
                    margin: 0;
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #172554, #2563eb);
                    padding: 20px;
                }

                .contenedor {
                    width: 100%;
                    max-width: 430px;
                    background: white;
                    padding: 40px 35px;
                    border-radius: 18px;
                    box-shadow: 0 15px 40px rgba(0,0,0,0.2);
                    text-align: center;
                }

                .logo {
                    color: #2563eb;
                    font-size: 28px;
                    font-weight: bold;
                    margin-bottom: 25px;
                }

                .icono {
                    width: 70px;
                    height: 70px;
                    margin: 0 auto 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    background: #dbeafe;
                    color: #2563eb;
                    font-size: 32px;
                }

                h2 {
                    color: #172554;
                    margin-bottom: 12px;
                    font-size: 25px;
                }

                .descripcion {
                    color: #64748b;
                    font-size: 14px;
                    line-height: 1.6;
                    margin-bottom: 25px;
                }

                input {
                    width: 100%;
                    padding: 14px;
                    border: 1px solid #cbd5e1;
                    border-radius: 9px;
                    font-size: 15px;
                    margin-bottom: 18px;
                    outline: none;
                }

                input:focus {
                    border-color: #2563eb;
                    box-shadow: 0 0 0 3px #dbeafe;
                }

                button {
                    width: 100%;
                    padding: 14px;
                    border: none;
                    border-radius: 9px;
                    background: #2563eb;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: 0.3s;
                }

                button:hover {
                    background: #1d4ed8;
                    transform: translateY(-2px);
                }

                .volver {
                    display: inline-block;
                    margin-top: 25px;
                    color: #2563eb;
                    text-decoration: none;
                    font-size: 14px;
                    font-weight: bold;
                }

                .volver:hover {
                    text-decoration: underline;
                }
            </style>
        </head>

        <body>
            <div class="contenedor">

                <div class="logo">TRANSIWEB</div>

                <div class="icono">✉</div>

                <h2>¿Olvidaste tu contraseña?</h2>

                <p class="descripcion">
                    No te preocupes. Ingresa el correo electrónico
                    asociado a tu cuenta y te enviaremos un enlace
                    para restablecer tu contraseña.
                </p>

                <form method="POST">
                    <input
                        type="email"
                        name="correo"
                        placeholder="Ingresa tu correo electrónico"
                        required
                    >

                    <button type="submit">
                        Enviar enlace de recuperación
                    </button>
                </form>

                <a href="/login.html" class="volver">
                    ← Volver al inicio de sesión
                </a>

            </div>
        </body>
        </html>
        """)

    correo = request.form.get("correo", "").strip().lower()

    if not correo:
        return "Debes ingresar tu correo electrónico.", 400

    conexion = None
    cursor = None
    usuario = None
    token = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, correo FROM usuarios WHERE correo = %s LIMIT 1",
            (correo,)
        )

        usuario = cursor.fetchone()

        if usuario:
            token = secrets.token_urlsafe(32)

            token_hash = hashlib.sha256(
                token.encode("utf-8")
            ).hexdigest()

            cursor.execute(
                """
                UPDATE password_reset_tokens
                SET used_at = NOW()
                WHERE usuario_id = %s AND used_at IS NULL
                """,
                (usuario["id"],)
            )

            cursor.execute(
                """
                INSERT INTO password_reset_tokens
                (usuario_id, token_hash, expires_at)
                VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 30 MINUTE))
                """,
                (usuario["id"], token_hash)
            )

            conexion.commit()

    except Exception:
        if conexion is not None:
            conexion.rollback()

        current_app.logger.exception(
            "Error al crear solicitud de recuperación"
        )

        return "No se pudo procesar la solicitud. Inténtalo más tarde.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()

    if usuario and token:

        base_url = os.getenv("TRANSIWEB_BASE_URL")
            
        if not base_url:
            base_url = "http://192.168.17.89:5000"

        enlace = (
            base_url.rstrip("/")
            + "/restablecer_password?token="
            + token
        )

        try:
            _enviar_correo_recuperacion(correo, enlace)

        except Exception:
            current_app.logger.exception(
                "No se pudo enviar el correo de recuperación"
            )

            conexion = None
            cursor = None

            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()

                cursor.execute(
                    """
                    UPDATE password_reset_tokens
                    SET used_at = NOW()
                    WHERE usuario_id = %s AND token_hash = %s
                    """,
                    (
                        usuario["id"],
                        hashlib.sha256(token.encode("utf-8")).hexdigest()
                    )
                )

                conexion.commit()

            except Exception:
                if conexion is not None:
                    conexion.rollback()

                current_app.logger.exception(
                    "No se pudo invalidar el token"
                )

            finally:
                if cursor is not None:
                    cursor.close()

                if conexion is not None and conexion.is_connected():
                    conexion.close()

            return "No se pudo enviar el correo. Revisa la configuración de Gmail.", 500

    return """
        <div style="
            font-family: Arial;
            text-align: center;
            margin: 100px auto;
            max-width: 450px;
        ">
            <h2 style="color: #172554;">
                Solicitud procesada
            </h2>

            <p style="color: #64748b;">
                Si el correo pertenece a una cuenta registrada,
                recibirás instrucciones para recuperar tu contraseña.
            </p>

            <a href="/login.html" style="
                color: #2563eb;
                text-decoration: none;
                font-weight: bold;
            ">
                Volver al inicio de sesión
            </a>
        </div>
    """



@auth.route("/restablecer_password", methods=["GET", "POST"])
def restablecer_password():

    if request.method == "GET":
        token = request.args.get("token", "").strip()

        if not token:
            return "El enlace no es válido.", 400

        return render_template_string("""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Nueva contraseña - Transiweb</title>
        </head>
        <body>
            <h2>Crear nueva contraseña</h2>

            <form method="POST">
                <input type="hidden" name="token" value="{{ token }}">

                <label>Nueva contraseña</label>
                <input type="password" name="password"
                       minlength="8" required>

                <label>Confirmar contraseña</label>
                <input type="password" name="confirmar_password"
                       minlength="8" required>

                <button type="submit">Cambiar contraseña</button>
            </form>
        </body>
        </html>
        """, token=token)

    token = request.form.get("token", "").strip()
    password = request.form.get("password", "")
    confirmar = request.form.get("confirmar_password", "")

    if not token:
        return "El enlace no es válido.", 400

    if len(password) < 8:
        return "La contraseña debe tener al menos 8 caracteres.", 400

    if password != confirmar:
        return "Las contraseñas no coinciden.", 400

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, usuario_id
            FROM password_reset_tokens
            WHERE token_hash = %s
              AND used_at IS NULL
              AND expires_at > NOW()
            LIMIT 1
            FOR UPDATE
            """,
            (token_hash,)
        )

        registro = cursor.fetchone()

        if not registro:
            conexion.rollback()
            return "El enlace venció o ya fue utilizado. Solicita uno nuevo.", 400

        password_segura = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            "UPDATE usuarios SET password = %s WHERE id = %s",
            (password_segura, registro["usuario_id"])
        )

        cursor.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = NOW()
            WHERE usuario_id = %s AND used_at IS NULL
            """,
            (registro["usuario_id"],)
        )

        conexion.commit()

        return """
            <h2>¡Contraseña actualizada!</h2>
            <p>Ya puedes iniciar sesión con tu nueva contraseña.</p>
            <a href="/login.html">Iniciar sesión</a>
        """

    except Exception:
        if conexion is not None:
            conexion.rollback()

        current_app.logger.exception(
            "Error al restablecer la contraseña"
        )
        return "No se pudo cambiar la contraseña. Inténtalo nuevamente.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()
