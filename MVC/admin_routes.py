
import mysql.connector

from flask import (
    Blueprint, abort, flash, redirect,
    render_template, request, session, url_for
)

from MVC.models.config.database import conectar_bd

admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates"
)


def admin_requerido():

    if not session.get("usuario_id"):
        return redirect("/login.html")

    if str(session.get("usuario_rol", "")).lower() not in (
        "admin", "administrador"
    ):
        abort(403)

    return None


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

            accion = request.form.get("accion")

            if accion == "agregar":

                nombre = request.form.get("nombre", "").strip()
                descripcion = request.form.get("descripcion", "").strip()

                if not nombre:
                    flash("Escribe el nombre del trámite.", "error")

                else:
                    cursor.execute(
                        """INSERT INTO tramites
                        (nombre, descripcion, estado)
                        VALUES (%s, %s, 'activo')""",
                        (nombre, descripcion)
                    )

                    conexion.commit()

                    flash("Trámite agregado correctamente.", "success")

            elif accion == "eliminar":

                tramite_id = request.form.get("eliminar_id", type=int)

                if tramite_id and tramite_id > 0:

                    cursor.execute(
                        "DELETE FROM tramites WHERE id = %s",
                        (tramite_id,)
                    )

                    conexion.commit()

                    flash("Operación de eliminación realizada.", "success")

                else:
                    flash("ID de trámite inválido.", "error")

            return redirect(url_for("admin.tramites"))

        cursor.execute("""
            SELECT id, nombre, descripcion, estado, creado_en
            FROM tramites
            ORDER BY id DESC
        """)

        datos = cursor.fetchall()

        return render_template(
            "admin/tramites.html",
            tramites=datos
        )

    except mysql.connector.Error as error:

        if conexion:
            conexion.rollback()

        flash(f"Error con la base de datos: {error}", "error")

        return redirect("/admin_lobby")

    finally:

        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()

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

import secrets
import hmac


@admin_bp.route("/admin/usuarios", methods=["GET", "POST"])
def usuarios():

    # Verificar que haya iniciado sesión
    if not session.get("usuario_id"):
        return redirect("/login.html")

    id_administrador = int(session.get("usuario_id"))

    # Verificar el rol directamente en la base de datos
    conexion = None
    cursor = None

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)

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

        # Crear token CSRF para proteger los formularios
        if not session.get("csrf_usuarios"):
            session["csrf_usuarios"] = secrets.token_hex(32)

        token_csrf = session["csrf_usuarios"]

        error = ""
        mensaje = ""

        # =================================================
        # PROCESAR FORMULARIOS
        # =================================================

        if request.method == "POST":

            token_recibido = request.form.get("csrf_token", "")

            if not hmac.compare_digest(token_csrf, token_recibido):
                abort(403)

            accion = request.form.get("accion", "")

            # ---------------------------------------------
            # EDITAR USUARIO
            # ---------------------------------------------

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
                    flash("El ID del usuario no es válido.", "error")

                elif not nombre or not correo or not identificacion:
                    flash("Todos los campos son obligatorios.", "error")

                elif len(nombre) > 150:
                    flash("El nombre no puede superar 150 caracteres.", "error")

                elif len(correo) > 254:
                    flash("El correo es demasiado largo.", "error")

                elif len(identificacion) > 50:
                    flash("La identificación es demasiado larga.", "error")

                elif "@" not in correo or "." not in correo.split("@")[-1]:
                    flash("Ingresa un correo electrónico válido.", "error")

                elif rol not in roles_permitidos:
                    flash("El rol seleccionado no es válido.", "error")

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
                        SELECT id FROM usuarios
                        WHERE correo = %s AND id <> %s
                        """,
                        (correo, id_usuario)
                    )

                    correo_existe = cursor.fetchone()

                    # Verificar identificación duplicada
                    cursor.execute(
                        """
                        SELECT id FROM usuarios
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

            # ---------------------------------------------
            # ELIMINAR USUARIO
            # ---------------------------------------------

            elif accion == "eliminar":

                id_usuario = request.form.get("id", type=int)

                if not id_usuario or id_usuario < 1:
                    flash("El ID del usuario no es válido.", "error")

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

            return redirect(url_for("admin.usuarios"))

        # =================================================
        # CONSULTAR USUARIO PARA EDITAR
        # =================================================

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
                flash("El usuario seleccionado no existe.", "error")

        # =================================================
        # LISTAR TODOS LOS USUARIOS
        # =================================================

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

        # Procesar actualización del estado
        if request.method == "POST":

            solicitud_id = request.form.get(
                "solicitud_id", type=int
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

                conexion.commit()

                flash(
                    "El estado de la solicitud se actualizó correctamente.",
                    "success"
                )

            return redirect(url_for("admin.solicitudes"))

        # Consultar solicitudes
        cursor.execute(
            """
            SELECT
                s.id,
                u.nombre AS nombre,
                u.correo,
                t.id AS tramite_id,
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