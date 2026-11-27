vscode_lsp_terminal_prompt_tracker= {}
import secrets
import hmac
import os
import mysql.connector

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for
)

from MVC.models.config.database import conectar_bd


# =========================================================
# CONFIGURACIÓN DEL BLUEPRINT
# =========================================================

admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates"
)


# =========================================================
# VERIFICAR ACCESO DE ADMINISTRADOR
# =========================================================

def admin_requerido():

    if not session.get("usuario_id"):
        return redirect("/login.html")

    if str(session.get("usuario_rol", "")).lower() not in (
        "admin",
        "administrador"
    ):
        abort(403)

    return None


# =========================================================
# GESTIÓN DE TRÁMITES
# =========================================================

@admin_bp.route("/admin/tramites", methods=["GET", "POST"])
def tramites():

    acceso = admin_requerido()

    if acceso:
        return acceso

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        if request.method == "POST":

            accion = request.form.get("accion", "")

            # AGREGAR TRÁMITE
            if accion == "agregar":

                nombre = request.form.get("nombre", "").strip()
                descripcion = request.form.get("descripcion", "").strip()

                if not nombre:
                    flash("Escribe el nombre del trámite.", "error")

                elif len(nombre) > 150:
                    flash(
                        "El nombre no puede superar los 150 caracteres.",
                        "error"
                    )

                else:
                    cursor.execute(
                        """
                        INSERT INTO tramites (nombre, descripcion, estado)
                        VALUES (%s, %s, 'activo')
                        """,
                        (nombre, descripcion or None)
                    )

                    conexion.commit()

                    flash(
                        "Trámite agregado correctamente.",
                        "success"
                    )

            # CAMBIAR ESTADO
            elif accion == "estado":

                tramite_id = request.form.get("tramite_id", type=int)
                estado = request.form.get("estado", "").strip()

                if not tramite_id or tramite_id <= 0:
                    flash("ID de trámite inválido.", "error")

                elif estado not in ("activo", "inactivo"):
                    flash("Estado seleccionado no válido.", "error")

                else:
                    cursor.execute(
                        """
                        UPDATE tramites
                        SET estado = %s
                        WHERE id = %s
                        """,
                        (estado, tramite_id)
                    )

                    if cursor.rowcount == 0:

                        cursor.execute(
                            "SELECT id FROM tramites WHERE id = %s",
                            (tramite_id,)
                        )

                        if cursor.fetchone() is None:
                            flash("Trámite no encontrado.", "error")
                        else:
                            flash(
                                "El trámite ya tenía ese estado.",
                                "success"
                            )

                    else:
                        flash(
                            "Estado actualizado correctamente.",
                            "success"
                        )

                    conexion.commit()

            # ELIMINAR TRÁMITE
            elif accion == "eliminar":

                tramite_id = request.form.get("eliminar_id", type=int)

                if not tramite_id or tramite_id <= 0:
                    flash("ID de trámite inválido.", "error")

                else:
                    cursor.execute(
                        "SELECT id FROM tramites WHERE id = %s",
                        (tramite_id,)
                    )

                    tramite = cursor.fetchone()

                    if not tramite:
                        flash("El trámite no existe.", "error")

                    else:
                        cursor.execute(
                            """
                            SELECT id
                            FROM solicitudes
                            WHERE tramite_id = %s
                            LIMIT 1
                            """,
                            (tramite_id,)
                        )

                        solicitud = cursor.fetchone()

                        if solicitud:
                            flash(
                                "No se puede eliminar este trámite porque "
                                "tiene solicitudes registradas. "
                                "Puedes cambiarlo a inactivo.",
                                "error"
                            )

                        else:
                            cursor.execute(
                                "DELETE FROM tramites WHERE id = %s",
                                (tramite_id,)
                            )

                            conexion.commit()

                            flash(
                                "Trámite eliminado correctamente.",
                                "success"
                            )

            else:
                flash(
                    "La acción solicitada no es válida.",
                    "error"
                )

            return redirect(url_for("admin.tramites"))

        # CONSULTAR TRÁMITES
        cursor.execute(
            """
            SELECT id, nombre, descripcion, estado, creado_en
            FROM tramites
            ORDER BY id DESC
            """
        )

        datos = cursor.fetchall()

        return render_template(
            "admin/tramites.html",
            tramites=datos
        )

    except mysql.connector.Error as error:

        if conexion:
            conexion.rollback()

        flash(
            f"Error con la base de datos: {error}",
            "error"
        )

        return redirect("/admin_lobby")

    finally:

        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()


# =========================================================
# EDITAR TRÁMITE
# =========================================================

@admin_bp.route(
    "/admin/editar_tramite/<int:id_tramite>",
    methods=["GET", "POST"]
)
def editar_tramite(id_tramite):

    acceso = admin_requerido()

    if acceso:
        return acceso

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, nombre, descripcion, estado
            FROM tramites
            WHERE id = %s
            """,
            (id_tramite,)
        )

        tramite = cursor.fetchone()

        if not tramite:
            flash("No se encontró el trámite.", "error")
            return redirect(url_for("admin.tramites"))

        error = ""

        if request.method == "POST":

            nombre = request.form.get("nombre", "").strip()
            descripcion = request.form.get("descripcion", "").strip()
            estado = request.form.get("estado", "")

            tramite["nombre"] = nombre
            tramite["descripcion"] = descripcion
            tramite["estado"] = estado

            if nombre == "":
                error = "Debes escribir el nombre del trámite."

            elif len(nombre) > 150:
                error = "El nombre no puede superar los 150 caracteres."

            elif estado not in ("activo", "inactivo"):
                error = "El estado seleccionado no es válido."

            else:
                cursor.execute(
                    """
                    UPDATE tramites
                    SET nombre = %s,
                        descripcion = %s,
                        estado = %s
                    WHERE id = %s
                    """,
                    (nombre, descripcion, estado, id_tramite)
                )

                conexion.commit()

                flash(
                    "Trámite actualizado correctamente.",
                    "success"
                )

                return redirect(url_for("admin.tramites"))

        return render_template(
            "admin/editar_tramite.html",
            tramite=tramite,
            error=error
        )

    except mysql.connector.Error as error:

        if conexion:
            conexion.rollback()

        flash(
            f"Error al editar el trámite: {error}",
            "error"
        )

        return redirect(url_for("admin.tramites"))

    finally:

        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()


# =========================================================
# GESTIÓN DE USUARIOS
# =========================================================

@admin_bp.route("/admin/usuarios", methods=["GET", "POST"])
def usuarios():

    if not session.get("usuario_id"):
        return redirect("/login.html")

    id_administrador = int(session.get("usuario_id"))

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        # Verificar el rol directamente en la base de datos
        cursor.execute(
            "SELECT rol FROM usuarios WHERE id = %s",
            (id_administrador,)
        )

        datos_admin = cursor.fetchone()

        if (
            not datos_admin
            or str(datos_admin["rol"]).lower()
            not in ("admin", "administrador")
        ):
            abort(403)

        # CREAR TOKEN CSRF
        if not session.get("csrf_usuarios"):
            session["csrf_usuarios"] = secrets.token_hex(32)

        token_csrf = session["csrf_usuarios"]

        # PROCESAR FORMULARIOS
        if request.method == "POST":

            token_recibido = request.form.get("csrf_token", "")

            if not hmac.compare_digest(token_csrf, token_recibido):
                abort(403)

            accion = request.form.get("accion", "")

            # EDITAR USUARIO
            if accion == "editar":

                id_usuario = request.form.get("id", type=int)
                nombre = request.form.get("nombre", "").strip()
                correo = request.form.get("correo", "").strip()
                identificacion = request.form.get(
                    "identificacion", ""
                ).strip()
                rol = request.form.get("rol", "").strip().lower()

                roles_permitidos = [
                    "admin",
                    "administrador",
                    "usuario",
                    "ciudadano"
                ]

                if not id_usuario or id_usuario < 1:
                    flash(
                        "El ID del usuario no es válido.",
                        "error"
                    )

                elif not nombre or not correo or not identificacion:
                    flash(
                        "Todos los campos son obligatorios.",
                        "error"
                    )

                elif len(nombre) > 150:
                    flash(
                        "El nombre no puede superar 150 caracteres.",
                        "error"
                    )

                elif len(correo) > 254:
                    flash(
                        "El correo es demasiado largo.",
                        "error"
                    )

                elif len(identificacion) > 50:
                    flash(
                        "La identificación es demasiado larga.",
                        "error"
                    )

                elif "@" not in correo or "." not in correo.split("@")[-1]:
                    flash(
                        "Ingresa un correo electrónico válido.",
                        "error"
                    )

                elif rol not in roles_permitidos:
                    flash(
                        "El rol seleccionado no es válido.",
                        "error"
                    )

                else:

                    # No permitir cambiar el propio rol
                    if id_usuario == id_administrador:

                        cursor.execute(
                            "SELECT rol FROM usuarios WHERE id = %s",
                            (id_usuario,)
                        )

                        rol_actual = cursor.fetchone()

                        if (
                            rol_actual
                            and rol != str(rol_actual["rol"]).lower()
                        ):
                            flash(
                                "No puedes cambiar tu propio rol.",
                                "error"
                            )

                            return redirect(url_for("admin.usuarios"))

                    # Verificar correo duplicado
                    cursor.execute(
                        """
                        SELECT id
                        FROM usuarios
                        WHERE correo = %s AND id <> %s
                        """,
                        (correo, id_usuario)
                    )

                    correo_existe = cursor.fetchone()

                    # Verificar identificación duplicada
                    cursor.execute(
                        """
                        SELECT id
                        FROM usuarios
                        WHERE identificacion = %s AND id <> %s
                        """,
                        (identificacion, id_usuario)
                    )

                    identificacion_existe = cursor.fetchone()

                    if correo_existe:
                        flash(
                            "Ese correo ya está registrado por otro usuario.",
                            "error"
                        )

                    elif identificacion_existe:
                        flash(
                            "Esa identificación ya pertenece a otro usuario.",
                            "error"
                        )

                    else:
                        cursor.execute(
                            """
                            UPDATE usuarios
                            SET nombre = %s,
                                correo = %s,
                                identificacion = %s,
                                rol = %s
                            WHERE id = %s
                            """,
                            (
                                nombre,
                                correo,
                                identificacion,
                                rol,
                                id_usuario
                            )
                        )

                        conexion.commit()

                        flash(
                            "Usuario actualizado correctamente.",
                            "success"
                        )

            # ELIMINAR USUARIO
            elif accion == "eliminar":

                id_usuario = request.form.get("id", type=int)

                if not id_usuario or id_usuario < 1:
                    flash(
                        "El ID del usuario no es válido.",
                        "error"
                    )

                elif id_usuario in (27, 28, id_administrador):
                    flash(
                        "No puedes eliminar una cuenta protegida.",
                        "error"
                    )

                else:
                    cursor.execute(
                        "DELETE FROM usuarios WHERE id = %s",
                        (id_usuario,)
                    )

                    if cursor.rowcount > 0:
                        conexion.commit()

                        flash(
                            "Usuario eliminado correctamente.",
                            "success"
                        )

                    else:
                        conexion.rollback()

                        flash(
                            "No se pudo eliminar el usuario. "
                            "Comprueba que exista y que no tenga "
                            "registros relacionados.",
                            "error"
                        )

            else:
                flash(
                    "La acción solicitada no es válida.",
                    "error"
                )

            return redirect(url_for("admin.usuarios"))

        # CONSULTAR USUARIO PARA EDITAR
        id_editar = request.args.get("editar", type=int)
        usuario_editar = None

        if id_editar and id_editar > 0:

            cursor.execute(
                """
                SELECT id, nombre, correo, identificacion, rol
                FROM usuarios
                WHERE id = %s
                """,
                (id_editar,)
            )

            usuario_editar = cursor.fetchone()

            if not usuario_editar:
                flash(
                    "El usuario seleccionado no existe.",
                    "error"
                )

        # LISTAR TODOS LOS USUARIOS
        cursor.execute(
            """
            SELECT id, nombre, correo, identificacion, rol, fecha_registro
            FROM usuarios
            ORDER BY id DESC
            """
        )

        lista_usuarios = cursor.fetchall()

        return render_template(
            "admin/usuarios.html",
            usuarios=lista_usuarios,
            usuario_editar=usuario_editar,
            token_csrf=token_csrf
        )

    except mysql.connector.Error as error:

        if conexion:
            conexion.rollback()

        flash(
            f"Error con la base de datos: {error}",
            "error"
        )

        return redirect("/admin_lobby")

    finally:

        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()


# =========================================================
# GESTIÓN DE SOLICITUDES
# =========================================================

@admin_bp.route("/admin/solicitudes", methods=["GET", "POST"])
def solicitudes():

    acceso = admin_requerido()

    if acceso:
        return acceso

    conexion = None
    cursor = None

    estados = {
        "pendiente": "Pendiente",
        "en_proceso": "En proceso",
        "aprobada": "Aprobada",
        "rechazada": "Rechazada"
    }

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        # ACTUALIZAR ESTADO DE SOLICITUD
        if request.method == "POST":

            solicitud_id = request.form.get(
                "solicitud_id",
                type=int
            )

            estado = request.form.get("estado", "")

            if not solicitud_id or solicitud_id <= 0:
                flash(
                    "El ID de la solicitud no es válido.",
                    "error"
                )

            elif estado not in estados:
                flash(
                    "El estado seleccionado no es válido.",
                    "error"
                )

            else:
                cursor.execute(
                    """
                    UPDATE solicitudes
                    SET estado = %s
                    WHERE id = %s
                    """,
                    (estado, solicitud_id)
                )

                if cursor.rowcount == 0:
                    flash(
                        "No se encontró la solicitud o ya tenía ese estado.",
                        "error"
                    )
                else:
                    flash(
                        "El estado de la solicitud se actualizó correctamente.",
                        "success"
                    )

                conexion.commit()

            return redirect(url_for("admin.solicitudes"))

        # CONSULTAR SOLICITUDES
        cursor.execute(
            """
            SELECT
                s.id,
                u.nombre AS nombre,
                u.correo,
                t.id AS tramite_id,
                t.nombre AS nombre_tramite,
                s.estado,
                s.fecha_solicitud
            FROM solicitudes s
            INNER JOIN usuarios u
                ON s.usuario_id = u.id
            INNER JOIN tramites t
                ON s.tramite_id = t.id
            ORDER BY s.fecha_solicitud DESC
            """
        )

        lista_solicitudes = cursor.fetchall()

        # CONSULTAR LOS PDF DE CADA SOLICITUD
        for solicitud in lista_solicitudes:

            cursor.execute(
                """
                SELECT id, nombre_archivo
                FROM documentos_solicitud
                WHERE solicitud_id = %s
                ORDER BY id
                """,
                (solicitud["id"],)
            )

            solicitud["documentos"] = cursor.fetchall()

        return render_template(
            "admin/solicitudes.html",
            solicitudes=lista_solicitudes,
            estados=estados
        )

    except mysql.connector.Error as error:

        if conexion:
            conexion.rollback()

        flash(
            f"Error con la base de datos: {error}",
            "error"
        )

        return redirect("/admin_lobby")

    finally:

        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()


# =========================================================
# ABRIR DOCUMENTO PDF
# =========================================================

@admin_bp.route("/admin/document/<int:documento_id>")
def ver_documento(documento_id):

    acceso = admin_requerido()

    if acceso:
        return acceso

    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

        # BUSCAR DOCUMENTO EN LA BASE DE DATOS
        cursor.execute(
            """
            SELECT nombre_archivo, ruta_archivo
            FROM documentos_solicitud
            WHERE id = %s
            """,
            (documento_id,)
        )

        documento = cursor.fetchone()

        if not documento:
            return "Documento no encontrado.", 404

        # OBTENER LA RUTA PRINCIPAL DEL PROYECTO
        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        # CARPETA PERMITIDA PARA LOS DOCUMENTOS
        carpeta = os.path.abspath(
            os.path.join(
                base_dir,
                "uploads",
                "solicitudes"
            )
        )

        # RUTA COMPLETA DEL PDF
        ruta = os.path.abspath(
            os.path.join(
                base_dir,
                documento["ruta_archivo"]
            )
        )

        # COMPROBAR QUE EL ARCHIVO ESTÉ DENTRO DE LA CARPETA PERMITIDA
        if os.path.commonpath([carpeta, ruta]) != carpeta:
            return "Ruta no permitida.", 403

        # COMPROBAR QUE EL ARCHIVO EXISTA
        if not os.path.isfile(ruta):
            return "El PDF no existe en el servidor.", 404

        # ABRIR PDF EN EL NAVEGADOR
        return send_file(
            ruta,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=documento["nombre_archivo"]
        )

    except Exception:
        current_app.logger.exception(
            "Error al abrir PDF"
        )

        return "No se pudo abrir el documento.", 500

    finally:

        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()
