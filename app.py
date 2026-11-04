from werkzeug.utils import secure_filename
import uuid

from flask import (
    Flask, send_from_directory, redirect,
    session, abort, render_template_string, request
)
from markupsafe import escape
from mysql.connector import IntegrityError
from MVC.models.config.database import conectar_bd
from MVC.models.auth import auth
from flask import render_template_string
import os


# ==========================================================
# CONFIGURACIÓN DE FLASK
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "MVC", "vista"),
    static_url_path="/vista"
)
from MVC.admin_routes import admin_bp
app.register_blueprint(admin_bp)

app.config["SECRET_KEY"] = "transiweb-clave-temporal-cambiar"

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
# VERIFICAR PERMISOS DE ADMINISTRADOR
# ==========================================================

def exigir_admin():
    if not session.get("usuario_id"):
        return redirect("/login.html")

    if session.get("usuario_rol") not in ("admin", "administrador"):
        abort(403)

    return None


# ==========================================================
# PLANTILLA HTML PARA LAS SECCIONES ADMINISTRATIVAS
# ==========================================================

def pagina_admin(titulo, contenido):
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>{escape(titulo)} | Transiweb</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                font-family: Arial, sans-serif;
                background: #F2F4F7;
                color: #0F1B33;
                margin: 0;
                padding: 25px;
            }}

            main {{
                max-width: 1150px;
                margin: 25px auto;
                padding: 25px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 5px 20px rgba(0,0,0,.05);
                overflow-x: auto;
            }}

            h1, h2 {{
                color: #227F87;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}

            th, td {{
                padding: 12px;
                border-bottom: 1px solid #ddd;
                text-align: left;
            }}

            th {{
                background: #227F87;
                color: white;
            }}

            input, select, textarea, button {{
                padding: 10px;
                margin: 5px 0;
                max-width: 100%;
                border-radius: 5px;
                border: 1px solid #ccc;
                font: inherit;
            }}

            input, textarea {{
                width: 100%;
            }}

            button, .boton {{
                background: #227F87;
                color: white;
                border: none;
                padding: 10px 14px;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
            }}

            button:hover, .boton:hover {{
                background: #176B3A;
            }}

            form {{
                margin: 5px 0;
            }}

            .volver {{
                display: inline-block;
                margin-bottom: 15px;
                color: #227F87;
            }}

            .formulario {{
                max-width: 600px;
                margin: 20px 0;
            }}

            .estado-form {{
                min-width: 150px;
            }}

            @media (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}

                main {{
                    padding: 15px;
                }}
            }}
        </style>
    </head>

    <body>
        <main>
            <a class="volver" href="/admin_lobby">
                ← Volver al panel administrativo
            </a>

            {contenido}
        </main>
    </body>
    </html>
    """


# ==========================================================
# PANEL PRINCIPAL DEL ADMINISTRADOR
# ==========================================================

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
# 1. GESTIONAR USUARIOS
# ==========================================================

@app.route("/admin/usuarios")
def admin_usuarios():
    respuesta = exigir_admin()

    if respuesta:
        return respuesta

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nombre, correo, identificacion,
                   fecha_registro, rol
            FROM usuarios
            ORDER BY id DESC
        """)

        usuarios = cursor.fetchall()
        filas = ""

        for u in usuarios:
            filas += f"""
            <tr>
                <td>{u['id']}</td>
                <td>{escape(str(u['nombre']))}</td>
                <td>{escape(str(u['correo']))}</td>
                <td>{escape(str(u['identificacion']))}</td>
                <td>{escape(str(u['rol']))}</td>
                <td>{escape(str(u['fecha_registro']))}</td>
                <td>
                    <a class="boton"
                       href="/admin/usuarios/editar/{u['id']}">
                        Editar
                    </a>
                </td>
            </tr>
            """

        contenido = f"""
            <h1>Gestionar usuarios</h1>

            <p>Usuarios registrados: {len(usuarios)}</p>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nombre</th>
                        <th>Correo</th>
                        <th>Identificación</th>
                        <th>Rol</th>
                        <th>Registro</th>
                        <th>Acciones</th>
                    </tr>
                </thead>

                <tbody>
                    {filas or '<tr><td colspan="7">No hay usuarios registrados.</td></tr>'}
                </tbody>
            </table>
        """

        return pagina_admin("Gestionar usuarios", contenido)

    except Exception:
        app.logger.exception("Error al consultar usuarios")
        return "No se pudieron consultar los usuarios.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ----------------------------------------------------------
# EDITAR USUARIOS
# ----------------------------------------------------------

@app.route(
    "/admin/usuarios/editar/<int:usuario_id>",
    methods=["GET", "POST"]
)
def editar_usuario(usuario_id):
    respuesta = exigir_admin()

    if respuesta:
        return respuesta

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nombre, correo, identificacion, rol
            FROM usuarios
            WHERE id = %s
        """, (usuario_id,))

        usuario = cursor.fetchone()

        if not usuario:
            return "Usuario no encontrado.", 404

        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            correo = request.form.get("correo", "").strip()
            identificacion = request.form.get(
                "identificacion", ""
            ).strip()
            rol = request.form.get("rol", "").strip()

            if not nombre or not correo or not identificacion:
                return "Todos los campos son obligatorios.", 400

            if len(nombre) > 100 or len(correo) > 100:
                return "El nombre o el correo supera el límite permitido.", 400

            if len(identificacion) > 50:
                return "La identificación supera el límite permitido.", 400

            if rol not in ("usuario", "admin"):
                return "El rol seleccionado no es válido.", 400

            if (
                usuario_id == session.get("usuario_id")
                and rol != "admin"
            ):
                return "No puedes quitarte tu propio rol de administrador.", 400

            cursor.execute("""
                UPDATE usuarios
                SET nombre = %s,
                    correo = %s,
                    identificacion = %s,
                    rol = %s
                WHERE id = %s
            """, (
                nombre,
                correo,
                identificacion,
                rol,
                usuario_id
            ))

            conexion.commit()

            # Actualiza el nombre de la sesión si el admin
            # modificó su propio nombre.
            if usuario_id == session.get("usuario_id"):
                session["usuario_nombre"] = nombre
                session["usuario_correo"] = correo

            return redirect("/admin/usuarios")

        nombre = escape(str(usuario["nombre"]))
        correo = escape(str(usuario["correo"]))
        identificacion = escape(str(usuario["identificacion"]))

        seleccionado_usuario = (
            "selected" if usuario["rol"] == "usuario" else ""
        )

        seleccionado_admin = (
            "selected" if usuario["rol"] == "admin" else ""
        )

        contenido = f"""
            <h1>Editar usuario #{usuario['id']}</h1>

            <form method="POST" class="formulario">

                <label>Nombre completo</label>
                <input
                    type="text"
                    name="nombre"
                    maxlength="100"
                    value="{nombre}"
                    required
                >

                <label>Correo electrónico</label>
                <input
                    type="email"
                    name="correo"
                    maxlength="100"
                    value="{correo}"
                    required
                >

                <label>Identificación</label>
                <input
                    type="text"
                    name="identificacion"
                    maxlength="50"
                    value="{identificacion}"
                    required
                >

                <label>Rol del usuario</label>
                <select name="rol" required>
                    <option value="usuario" {seleccionado_usuario}>
                        Usuario
                    </option>

                    <option value="admin" {seleccionado_admin}>
                        Administrador
                    </option>
                </select>

                <br>

                <button type="submit">Guardar cambios</button>

                <a class="boton" href="/admin/usuarios">
                    Cancelar
                </a>
            </form>
        """

        return pagina_admin("Editar usuario", contenido)

    except IntegrityError:
        if conexion is not None:
            conexion.rollback()

        return (
            "No se pudo guardar. El correo o la identificación "
            "ya pueden pertenecer a otro usuario.",
            400
        )

    except Exception:
        if conexion is not None:
            conexion.rollback()

        app.logger.exception("Error al editar usuario")
        return "No se pudo editar el usuario.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ==========================================================
# 2. GESTIONAR TRÁMITES
# ==========================================================

@app.route("/admin/tramites", methods=["GET", "POST"])
def admin_tramites():
    respuesta = exigir_admin()

    if respuesta:
        return respuesta

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        if request.method == "POST":
            accion = request.form.get("accion", "")

            # Registrar un trámite
            if accion == "crear":
                nombre = request.form.get("nombre", "").strip()
                descripcion = request.form.get(
                    "descripcion", ""
                ).strip()

                if not nombre:
                    return "El nombre del trámite es obligatorio.", 400

                if len(nombre) > 150:
                    return "El nombre supera los 150 caracteres.", 400

                cursor.execute("""
                    INSERT INTO tramites (nombre, descripcion)
                    VALUES (%s, %s)
                """, (nombre, descripcion or None))

                conexion.commit()

                return redirect("/admin/tramites")

            # Cambiar el estado de un trámite
            elif accion == "estado":
                tramite_id = request.form.get(
                    "tramite_id", type=int
                )
                estado = request.form.get("estado", "")

                if not tramite_id:
                    return "El ID del trámite no es válido.", 400

                if estado not in ("activo", "inactivo"):
                    return "El estado seleccionado no es válido.", 400

                cursor.execute("""
                    UPDATE tramites
                    SET estado = %s
                    WHERE id = %s
                """, (estado, tramite_id))

                if cursor.rowcount == 0:
                    cursor.execute("""
                        SELECT id FROM tramites WHERE id = %s
                    """, (tramite_id,))

                    if cursor.fetchone() is None:
                        return "Trámite no encontrado.", 404

                conexion.commit()

                return redirect("/admin/tramites")

            else:
                return "Acción no válida.", 400

        cursor.execute("""
            SELECT id, nombre, descripcion, estado, creado_en
            FROM tramites
            ORDER BY id DESC
        """)

        tramites = cursor.fetchall()
        filas = ""

        for t in tramites:
            nombre = escape(str(t["nombre"]))
            descripcion = escape(str(t["descripcion"] or ""))
            estado_actual = escape(str(t["estado"]))
            fecha = escape(str(t["creado_en"]))

            seleccionado_activo = (
                "selected" if t["estado"] == "activo" else ""
            )

            seleccionado_inactivo = (
                "selected" if t["estado"] == "inactivo" else ""
            )

            filas += f"""
            <tr>
                <td>{t['id']}</td>
                <td>{nombre}</td>
                <td>{descripcion}</td>
                <td>{estado_actual}</td>
                <td>{fecha}</td>
                <td>
                    <form method="POST">
                        <input
                            type="hidden"
                            name="accion"
                            value="estado"
                        >

                        <input
                            type="hidden"
                            name="tramite_id"
                            value="{t['id']}"
                        >

                        <select name="estado">
                            <option value="activo" {seleccionado_activo}>
                                Activo
                            </option>

                            <option value="inactivo" {seleccionado_inactivo}>
                                Inactivo
                            </option>
                        </select>

                        <button type="submit">Guardar</button>
                    </form>
                </td>
            </tr>
            """

        contenido = f"""
            <h1>Gestionar trámites</h1>

            <h2>Registrar nuevo trámite</h2>

            <form method="POST" class="formulario">
                <input type="hidden" name="accion" value="crear">

                <label>Nombre del trámite</label>
                <input
                    type="text"
                    name="nombre"
                    maxlength="150"
                    required
                >

                <label>Descripción</label>
                <textarea
                    name="descripcion"
                    rows="4"
                ></textarea>

                <button type="submit">Registrar trámite</button>
            </form>

            <h2>Trámites registrados: {len(tramites)}</h2>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nombre</th>
                        <th>Descripción</th>
                        <th>Estado</th>
                        <th>Fecha de creación</th>
                        <th>Acciones</th>
                    </tr>
                </thead>

                <tbody>
                    {filas or '<tr><td colspan="6">No hay trámites registrados.</td></tr>'}
                </tbody>
            </table>
        """

        return pagina_admin("Gestionar trámites", contenido)

    except Exception:
        if conexion is not None:
            conexion.rollback()

        app.logger.exception("Error al gestionar trámites")
        return "No se pudieron gestionar los trámites.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ==========================================================
# 3. GESTIONAR SOLICITUDES
# ==========================================================

@app.route("/admin/solicitudes", methods=["GET", "POST"])
def admin_solicitudes():
    respuesta = exigir_admin()

    if respuesta:
        return respuesta

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        if request.method == "POST":
            solicitud_id = request.form.get(
                "solicitud_id", type=int
            )

            nuevo_estado = request.form.get("estado", "")

            estados_validos = (
                "pendiente",
                "en_proceso",
                "aprobada",
                "rechazada"
            )

            if not solicitud_id:
                return "El ID de la solicitud no es válido.", 400

            if nuevo_estado not in estados_validos:
                return "El estado seleccionado no es válido.", 400

            cursor.execute("""
                UPDATE solicitudes
                SET estado = %s
                WHERE id = %s
            """, (nuevo_estado, solicitud_id))

            if cursor.rowcount == 0:
                cursor.execute("""
                    SELECT id FROM solicitudes WHERE id = %s
                """, (solicitud_id,))

                if cursor.fetchone() is None:
                    return "Solicitud no encontrada.", 404

            conexion.commit()

            return redirect("/admin/solicitudes")

        cursor.execute("""
            SELECT
                s.id,
                s.usuario_id,
                s.tramite_id,
                s.estado,
                s.fecha_solicitud,
                u.nombre AS nombre_usuario,
                u.correo AS correo_usuario,
                t.nombre AS nombre_tramite
            FROM solicitudes AS s
            INNER JOIN usuarios AS u
                ON u.id = s.usuario_id
            INNER JOIN tramites AS t
                ON t.id = s.tramite_id
            ORDER BY s.fecha_solicitud DESC
        """)

        solicitudes = cursor.fetchall()
        filas = ""

        etiquetas = {
            "pendiente": "Pendiente",
            "en_proceso": "En proceso",
            "aprobada": "Aprobada",
            "rechazada": "Rechazada"
        }

        for s in solicitudes:
            opciones = ""

            for estado, etiqueta in etiquetas.items():
                seleccionado = (
                    "selected" if s["estado"] == estado else ""
                )

                opciones += f"""
                    <option value="{estado}" {seleccionado}>
                        {etiqueta}
                    </option>
                """

            filas += f"""
            <tr>
                <td>{s['id']}</td>
                <td>{escape(str(s['nombre_usuario']))}</td>
                <td>{escape(str(s['correo_usuario']))}</td>
                <td>{escape(str(s['nombre_tramite']))}</td>
                <td>{escape(str(s['fecha_solicitud']))}</td>
                <td>
                    <form method="POST" class="estado-form">
                        <input
                            type="hidden"
                            name="solicitud_id"
                            value="{s['id']}"
                        >

                        <select name="estado">
                            {opciones}
                        </select>

                        <button type="submit">Actualizar</button>
                    </form>
                </td>
            </tr>
            """

        contenido = f"""
            <h1>Gestionar solicitudes</h1>

            <p>Solicitudes encontradas: {len(solicitudes)}</p>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Ciudadano</th>
                        <th>Correo</th>
                        <th>Trámite</th>
                        <th>Fecha de solicitud</th>
                        <th>Estado y acciones</th>
                    </tr>
                </thead>

                <tbody>
                    {filas or '<tr><td colspan="6">No hay solicitudes registradas.</td></tr>'}
                </tbody>
            </table>
        """

        return pagina_admin("Gestionar solicitudes", contenido)

    except Exception:
        if conexion is not None:
            conexion.rollback()

        app.logger.exception("Error al gestionar solicitudes")
        return "No se pudieron gestionar las solicitudes.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()


# ==========================================================
# EJECUTAR APLICACIÓN
# ==========================================================


# ==========================================================
# CERRAR SESIÓN
# ==========================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login.html")

@app.route("/registro")
def registro():
    return send_from_directory(
        os.path.join(BASE_DIR, "MVC", "models"),
        "registro.html"
    )

@app.route("/control/<path:filename>")
def archivos_control(filename):
    carpeta_control = os.path.join(BASE_DIR, "MVC", "control")
    return send_from_directory(carpeta_control, filename)


import secrets
from flask import request, render_template_string, redirect, url_for, abort, flash

@app.route("/admin/usuarios", methods=["GET", "POST"])
def gestionar_usuarios():

    # Verificar que haya una sesión iniciada
    if "usuario_id" not in session:
        return redirect("/login.html")

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    try:
        # Verificar que el usuario sea administrador
        cursor.execute(
            "SELECT rol FROM usuarios WHERE id = %s",
            (session["usuario_id"],)
        )
        administrador = cursor.fetchone()

        if not administrador or administrador["rol"].lower() not in ["admin", "administrador"]:
            abort(403)

        # Crear token CSRF
        if "csrf_usuarios" not in session:
            session["csrf_usuarios"] = secrets.token_hex(32)

        error = ""

        # Procesar formularios
        if request.method == "POST":

            token = request.form.get("csrf_token", "")

            if not secrets.compare_digest(token, session["csrf_usuarios"]):
                abort(403)

            accion = request.form.get("accion", "")

            if accion == "editar":

                id_usuario = request.form.get("id", type=int)
                nombre = request.form.get("nombre", "").strip()
                correo = request.form.get("correo", "").strip()
                identificacion = request.form.get("identificacion", "").strip()
                rol = request.form.get("rol", "").strip().lower()

                roles = ["admin", "administrador", "usuario", "ciudadano"]

                if not id_usuario or not nombre or not correo or not identificacion:
                    error = "Todos los campos son obligatorios."

                elif rol not in roles:
                    error = "El rol seleccionado no es válido."

                elif id_usuario == int(session["usuario_id"]) and rol not in ["admin", "administrador"]:
                    error = "No puedes cambiar tu propio rol de administrador."

                else:
                    cursor.execute(
                        "SELECT id FROM usuarios WHERE correo = %s AND id <> %s",
                        (correo, id_usuario)
                    )
                    correo_existe = cursor.fetchone()

                    cursor.execute(
                        "SELECT id FROM usuarios WHERE identificacion = %s AND id <> %s",
                        (identificacion, id_usuario)
                    )
                    identificacion_existe = cursor.fetchone()

                    if correo_existe:
                        error = "Ese correo ya está registrado."

                    elif identificacion_existe:
                        error = "Esa identificación ya está registrada."

                    else:
                        cursor.execute("""
                            UPDATE usuarios
                            SET nombre = %s, correo = %s,
                                identificacion = %s, rol = %s
                            WHERE id = %s
                        """, (nombre, correo, identificacion, rol, id_usuario))

                        conexion.commit()
                        return redirect("/admin/usuarios?mensaje=editado")

            elif accion == "eliminar":

                id_usuario = request.form.get("id", type=int)

                if not id_usuario or id_usuario in [27, int(session["usuario_id"])]:
                    error = "No puedes eliminar esta cuenta."

                else:
                    cursor.execute(
                        "DELETE FROM usuarios WHERE id = %s",
                        (id_usuario,)
                    )

                    if cursor.rowcount > 0:
                        conexion.commit()
                        return redirect("/admin/usuarios?mensaje=eliminado")
                    else:
                        error = "No se pudo eliminar el usuario."

        # Consultar usuarios
        cursor.execute("""
            SELECT id, nombre, correo, identificacion, rol, fecha_registro
            FROM usuarios
            ORDER BY id DESC
        """)

        usuarios = cursor.fetchall()

        # Consultar usuario para editar
        usuario_editar = None
        id_editar = request.args.get("editar", type=int)

        if id_editar:
            cursor.execute("""
                SELECT id, nombre, correo, identificacion, rol
                FROM usuarios WHERE id = %s
            """, (id_editar,))
            usuario_editar = cursor.fetchone()

        mensaje = request.args.get("mensaje", "")

        return render_template_string("""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Gestionar usuarios | Transiweb</title>
            <style>
                body { font-family: Arial; background: #F2F4F7; margin: 0; color: #16223F; }
                header { background: #227F87; color: white; padding: 22px 5%; }
                main { max-width: 1200px; margin: 35px auto; padding: 20px; }
                .tarjeta { background: white; padding: 22px; margin: 20px 0; border-radius: 12px; }
                table { width: 100%; border-collapse: collapse; min-width: 850px; }
                th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }
                th { background: #227F87; color: white; }
                .tabla { overflow-x: auto; }
                input, select { padding: 10px; margin: 6px 0 14px; width: 100%; box-sizing: border-box; }
                button, .boton { padding: 9px 12px; border: 0; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
                .editar { background: #227F87; color: white; }
                .eliminar { background: #E63946; color: white; }
                .aviso { background: #E4F7E9; padding: 12px; }
                .error { background: #FDE8E8; padding: 12px; }
            </style>
        </head>
        <body>
            <header><h2>TRANSIWEB - Panel administrativo</h2></header>
            <main>
                <a href="/admin_lobby">← Volver al panel</a>
                <h1>Gestionar usuarios</h1>

                {% if mensaje == "editado" %}
                    <p class="aviso">Usuario actualizado correctamente.</p>
                {% elif mensaje == "eliminado" %}
                    <p class="aviso">Usuario eliminado correctamente.</p>
                {% endif %}

                {% if error %}
                    <p class="error">{{ error }}</p>
                {% endif %}

                <section class="tarjeta">
                    <h3>Usuarios registrados: {{ usuarios|length }}</h3>
                </section>

                {% if usuario_editar %}
                <section class="tarjeta">
                    <h2>Editar usuario #{{ usuario_editar.id }}</h2>
                    <form method="POST">
                        <input type="hidden" name="csrf_token" value="{{ token }}">
                        <input type="hidden" name="accion" value="editar">
                        <input type="hidden" name="id" value="{{ usuario_editar.id }}">

                        <label>Nombre</label>
                        <input name="nombre" value="{{ usuario_editar.nombre }}" required>

                        <label>Correo</label>
                        <input type="email" name="correo" value="{{ usuario_editar.correo }}" required>

                        <label>Identificación</label>
                        <input name="identificacion" value="{{ usuario_editar.identificacion }}" required>

                        <label>Rol</label>
                        <select name="rol">
                            {% for r in ["usuario", "ciudadano", "admin", "administrador"] %}
                                <option value="{{ r }}" {% if usuario_editar.rol|lower == r %}selected{% endif %}>{{ r }}</option>
                            {% endfor %}
                        </select>

                        <button class="editar">Guardar cambios</button>
                        <a class="boton" href="/admin/usuarios">Cancelar</a>
                    </form>
                </section>
                {% endif %}

                <section class="tarjeta">
                    <h2>Listado de usuarios</h2>
                    <div class="tabla">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th><th>Nombre</th><th>Correo</th>
                                <th>Identificación</th><th>Rol</th>
                                <th>Fecha</th><th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                        {% for u in usuarios %}
                            <tr>
                                <td>{{ u.id }}</td>
                                <td>{{ u.nombre }}</td>
                                <td>{{ u.correo }}</td>
                                <td>{{ u.identificacion }}</td>
                                <td>{{ u.rol }}</td>
                                <td>{{ u.fecha_registro }}</td>
                                <td>
                                    <a class="boton editar" href="/admin/usuarios?editar={{ u.id }}">Editar</a>

                                    {% if u.id != 27 and u.id != administrador_id %}
                                    <form method="POST" style="display:inline" onsubmit="return confirm('¿Eliminar este usuario?')">
                                        <input type="hidden" name="csrf_token" value="{{ token }}">
                                        <input type="hidden" name="accion" value="eliminar">
                                        <input type="hidden" name="id" value="{{ u.id }}">
                                        <button class="eliminar">Eliminar</button>
                                    </form>
                                    {% else %}
                                        Protegido
                                    {% endif %}
                                </td>
                            </tr>
                        {% else %}
                            <tr><td colspan="7">No hay usuarios registrados.</td></tr>
                        {% endfor %}
                        </tbody>
                    </table>
                    </div>
                </section>
            </main>
        </body>
        </html>
        """, usuarios=usuarios, usuario_editar=usuario_editar,
            mensaje=mensaje, error=error,
            token=session["csrf_usuarios"],
            administrador_id=int(session["usuario_id"]))

    finally:
        cursor.close()
        conexion.close()
        
@app.route("/panel_usuario")
def panel_usuario():
    if "usuario_id" not in session:
        return redirect("/login.html")

    if session.get("usuario_rol") in ("admin", "administrador"):
        return redirect("/admin_lobby")

    ruta = os.path.join(BASE_DIR, "MVC", "models", "lobby.html")

    with open(ruta, "r", encoding="utf-8") as archivo:
        contenido = archivo.read()

    return render_template_string(contenido) 

@app.route("/consultar_tramites")
def consultar_tramites():
    if "usuario_id" not in session:
        return redirect("/login.html")

    ruta = os.path.join(
        BASE_DIR, "MVC", "models", "consultar_tramites.html"
    )

    return send_from_directory(
        os.path.dirname(ruta),
        os.path.basename(ruta)
    )


@app.route("/como_funciona")
def como_funciona():
    if "usuario_id" not in session:
        return redirect("/login.html")

    ruta = os.path.join(
        BASE_DIR, "MVC", "models", "como_funciona.html"
    )

    return send_from_directory(
        os.path.dirname(ruta),
        os.path.basename(ruta)
    ) 

@app.route("/logout")
def cerrar_sesion():
    session.clear()
    return redirect("/login.html")

@app.route("/inicio")
def pagina_principal():
    return send_from_directory(
        os.path.join(BASE_DIR, "MVC", "models"),
        "index.html"
    ) 
    
import re
import bcrypt
from flask import request, redirect, send_from_directory
from mysql.connector import IntegrityError


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
    identificacion = request.form.get("identificacion", "").strip()
    password = request.form.get("password", "")

    if not nombre or not correo or not identificacion or not password:
        return "Todos los campos son obligatorios.", 400

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        return "El correo electrónico no es válido.", 400

    if len(password) > 72:
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
        return "El correo o la identificación ya están registrados.", 409

    except Exception:
        if conexion:
            conexion.rollback()
        app.logger.exception("Error al registrar usuario")
        return "No se pudo crear la cuenta. Intenta nuevamente.", 500

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close() 
            
@app.route("/admin/editar_tramite/<int:id>", methods=["GET", "POST"])
def editar_tramite(id):

    if "usuario_id" not in session:
        return redirect("/login.html")

    if session.get("usuario_rol") not in ("admin", "administrador"):
        return redirect("/panel_usuario")

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        if request.method == "POST":

            nombre = request.form.get("nombre", "").strip()
            descripcion = request.form.get("descripcion", "").strip()
            estado = request.form.get("estado", "").strip()

            if not nombre:
                return "Debes escribir el nombre del trámite.", 400

            if estado not in ("activo", "inactivo"):
                return "El estado seleccionado no es válido.", 400

            cursor.execute(
                """
                UPDATE tramites
                SET nombre = %s, descripcion = %s, estado = %s
                WHERE id = %s
                """,
                (nombre, descripcion, estado, id)
            )

            conexion.commit()

            return redirect("/admin/tramites?editado=1")

        cursor.execute(
            """
            SELECT id, nombre, descripcion, estado
            FROM tramites
            WHERE id = %s
            """,
            (id,)
        )

        tramite = cursor.fetchone()

        if not tramite:
            return "No se encontró el trámite solicitado.", 404

        return render_template_string("""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Editar trámite | Transiweb</title>

            <style>
                * { box-sizing: border-box; }

                body {
                    margin: 0;
                    padding: 30px 16px;
                    font-family: Arial, sans-serif;
                    background: #f2f5f9;
                }

                .contenedor {
                    max-width: 650px;
                    margin: auto;
                    padding: 25px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 18px rgba(0,0,0,.08);
                }

                label {
                    display: block;
                    margin: 16px 0 7px;
                    font-weight: bold;
                }

                input, textarea, select {
                    width: 100%;
                    padding: 11px;
                    border: 1px solid #ccd5e0;
                    border-radius: 6px;
                    font: inherit;
                }

                textarea {
                    min-height: 120px;
                    resize: vertical;
                }

                button {
                    margin-top: 20px;
                    padding: 12px 18px;
                    border: 0;
                    border-radius: 6px;
                    background: #227F87;
                    color: white;
                    font-weight: bold;
                    cursor: pointer;
                }

                .volver {
                    display: inline-block;
                    margin-bottom: 20px;
                    color: #1769aa;
                    text-decoration: none;
                }
            </style>
        </head>

        <body>
        <main class="contenedor">

            <a class="volver" href="/admin/tramites">
                ← Volver a trámites
            </a>

            <h1>Editar trámite #{{ tramite.id }}</h1>

            <form method="POST">

                <label for="nombre">Nombre del trámite</label>
                <input type="text" id="nombre" name="nombre"
                       maxlength="150" required
                       value="{{ tramite.nombre }}">

                <label for="descripcion">Descripción</label>
                <textarea id="descripcion"
                          name="descripcion">{{ tramite.descripcion or "" }}</textarea>

                <label for="estado">Estado</label>
                <select id="estado" name="estado" required>
                    <option value="activo"
                        {% if tramite.estado == "activo" %}selected{% endif %}>
                        Activo
                    </option>

                    <option value="inactivo"
                        {% if tramite.estado == "inactivo" %}selected{% endif %}>
                        Inactivo
                    </option>
                </select>

                <button type="submit">Guardar cambios</button>

            </form>
        </main>
        </body>
        </html>
        """, tramite=tramite)

    except Exception:
        if conexion:
            conexion.rollback()

        app.logger.exception("Error al editar trámite")
        return "No se pudo procesar el trámite.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()  
            
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

    if "usuario_id" not in session:
        return redirect("/login.html")

    tramite_id = request.form.get("tramite_id", type=int)

    archivos = [
        archivo for archivo in request.files.getlist("documentos")
        if archivo and archivo.filename
    ]

    if not tramite_id:
        return "Debes seleccionar un trámite.", 400

    if not archivos:
        return "Debes adjuntar al menos un documento PDF.", 400

    if len(archivos) > 20:
        return "Solo puedes adjuntar hasta 20 documentos.", 400

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

        # Carpeta donde se guardarán los PDF.
        carpeta = os.path.join(
            BASE_DIR,
            "uploads",
            "solicitudes"
        )

        os.makedirs(carpeta, exist_ok=True)

        # Guardar cada documento.
        for archivo in archivos:

            nombre_original = secure_filename(archivo.filename)

            if not nombre_original:
                raise ValueError("Nombre de archivo no válido.")

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

        return redirect("/solicitar_tramite?enviado=1")

    except Exception:
        if conexion is not None:
            conexion.rollback()

        # Eliminar archivos si ocurrió un error.
        for ruta in archivos_guardados:
            if os.path.exists(ruta):
                os.remove(ruta)

        app.logger.exception("Error al enviar documentación")

        return "No se pudo registrar la solicitud.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexion is not None and conexion.is_connected():
            conexion.close()
              
if __name__ == "__main__":
    app.run(debug=True)
