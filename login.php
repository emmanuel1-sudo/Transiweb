<?php

session_start();

require_once "conexion.php";

if ($_SERVER["REQUEST_METHOD"] !== "POST") {
    header("Location: login.html");
    exit;
}

$correo = trim($_POST["correo"] ?? "");
$password = $_POST["password"] ?? "";

if ($correo === "" || $password === "") {
    exit("Debes ingresar el correo y la contraseña.");
}

$sql = "SELECT id, nombre, correo, password
        FROM usuarios
        WHERE correo = ?
        LIMIT 1";

$stmt = $conexion->prepare($sql);

if (!$stmt) {
    exit("Error al preparar la consulta.");
}

$stmt->bind_param("s", $correo);
$stmt->execute();

$resultado = $stmt->get_result();

if ($usuario = $resultado->fetch_assoc()) {

    if (password_verify($password, $usuario["password"])) {

        session_regenerate_id(true);

        $_SESSION["usuario_id"] = $usuario["id"];
        $_SESSION["usuario_nombre"] = $usuario["nombre"];
        $_SESSION["usuario_correo"] = $usuario["correo"];

        header("Location: lobby.php");
        exit;

    }
}

$stmt->close();
$conexion->close();

header("Location: login.html?
error=credenciales");
?>