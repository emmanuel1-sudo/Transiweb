
<?php

require_once __DIR__ . "/../models/usuario.php";

class UsuarioController
{
    private $usuario;

    public function __construct($conexion)
    {
        $this->usuario = new Usuario($conexion);
    }

    // Registrar un usuario
    public function registrar()
    {
        if ($_SERVER["REQUEST_METHOD"] !== "POST") {
            header("Location: /Transiweb/registro.html");
            exit;
        }

        $nombre = trim($_POST["nombre"] ?? "");
        $correo = trim($_POST["correo"] ?? "");
        $identificacion = trim($_POST["identificacion"] ?? "");
        $password = $_POST["password"] ?? "";

        // Validar campos
        if (
            $nombre === "" ||
            $correo === "" ||
            $identificacion === "" ||
            $password === ""
        ) {
            header("Location: /Transiweb/registro.html?error=campos");
            exit;
        }

        // Validar correo
        if (!filter_var($correo, FILTER_VALIDATE_EMAIL)) {
            header("Location: /Transiweb/registro.html?error=correo");
            exit;
        }

        // Comprobar si el correo ya existe
        if ($this->usuario->buscarPorCorreo($correo)) {
            header("Location: /Transiweb/registro.html?error=correo_existente");
            exit;
        }

        // Guardar usuario
        $resultado = $this->usuario->registrar(
            $nombre,
            $correo,
            $identificacion,
            $password
        );

        if ($resultado) {
            header("Location: /Transiweb/login.html?registro=exitoso");
            exit;
        }

        header("Location: /Transiweb/registro.html?error=registro");
        exit;
    }

    // Iniciar sesión
    public function iniciarSesion()
    {
        if ($_SERVER["REQUEST_METHOD"] !== "POST") {
            header("Location: /Transiweb/login.html");
            exit;
        }

        $correo = trim($_POST["correo"] ?? "");
        $password = $_POST["password"] ?? "";

        // Validar campos
        if ($correo === "" || $password === "") {
            header("Location: /Transiweb/login.html?error=campos");
            exit;
        }

        // Verificar credenciales
        $usuario = $this->usuario->iniciarSesion(
            $correo,
            $password
        );

        if (!$usuario) {
            header("Location: /Transiweb/login.html?error=credenciales");
            exit;
        }

        // Crear sesión
        if (session_status() !== PHP_SESSION_ACTIVE) {
            session_start();
        }

        session_regenerate_id(true);

        $_SESSION["usuario_id"] = $usuario["id"];
        $_SESSION["usuario_nombre"] = $usuario["nombre"];
        $_SESSION["usuario_correo"] = $usuario["correo"];

        header("Location: /Transiweb/lobby.php");
        exit;
    }
}
