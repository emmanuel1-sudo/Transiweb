
import bcrypt


class Usuario:

    def __init__(self, conexion):
        self.conexion = conexion

    # Registrar un usuario nuevo
    def registrar(self, nombre, correo, identificacion, password):

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        sql = """
            INSERT INTO usuarios
            (nombre, correo, identificacion, password)
            VALUES (%s, %s, %s, %s)
        """

        cursor = self.conexion.cursor()

        try:
            cursor.execute(
                sql,
                (nombre, correo, identificacion, password_hash)
            )

            self.conexion.commit()
            return True

        except Exception as error:
            print("Error al registrar usuario:", error)
            self.conexion.rollback()
            return False

        finally:
            cursor.close()

    # Buscar usuario por correo
    def buscar_por_correo(self, correo):

        sql = """
            SELECT id, nombre, correo, identificacion, password
            FROM usuarios
            WHERE correo = %s
            LIMIT 1
        """

        cursor = self.conexion.cursor(dictionary=True)

        try:
            cursor.execute(sql, (correo,))
            return cursor.fetchone()

        finally:
            cursor.close()

    # Iniciar sesión
    def iniciar_sesion(self, correo, password):

        usuario = self.buscar_por_correo(correo)

        if not usuario:
            return False

        password_guardada = usuario["password"]

        if isinstance(password_guardada, str):
            password_guardada = password_guardada.encode("utf-8")

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            password_guardada
        ):
            return False

        usuario.pop("password", None)

        return usuario
