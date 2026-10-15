<?php

class Usuario
{
    private $conexion;

    public function __construct($conexion)
    {
        $this->conexion = $conexion;
    }

    // Registrar un usuario nuevo
    public function registrar($nombre, $correo, $identificacion, $password)
    {
        $passwordHash = password_hash($password, PASSWORD_DEFAULT);

        $sql = "INSERT INTO usuarios
                (nombre, correo, identificacion, password)
                VALUES (?, ?, ?, ?)";

        $stmt = $this->conexion->prepare($sql);

        if (!$stmt) {
            return false;
        }

        $stmt->bind_param(
            "ssss",
            $nombre,
            $correo,
            $identificacion,
            $passwordHash
        );

        $resultado = $stmt->execute();
        $stmt->close();

        return $resultado;
    }

    // Buscar un usuario por correo electrónico
    public function buscarPorCorreo($correo)
    {
        $sql = "SELECT id, nombre, correo, identificacion, password
                FROM usuarios
                WHERE correo = ?
                LIMIT 1";

        $stmt = $this->conexion->prepare($sql);

        if (!$stmt) {
            return null;
        }

        $stmt->bind_param("s", $correo);
        $stmt->execute();

        $resultado = $stmt->get_result();
        $usuario = $resultado->fetch_assoc();

        $stmt->close();

        return $usuario ?: null;
    }

    // Validar las credenciales del usuario
    public function iniciarSesion($correo, $password)
    {
        $usuario = $this->buscarPorCorreo($correo);

        if (!$usuario) {
            return false;
        }

        if (!password_verify($password, $usuario["password"])) {
            return false;
        }

        // No devolver el hash de la contraseña
        unset($usuario["password"]);

        return $usuario;
    }
}