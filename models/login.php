<?php

session_start();

require_once __DIR__ . "/../models/conexion.php";

if ($_SERVER["REQUEST_METHOD"] !== "POST") {
    header("Location: login.html");
    exit;
}

$correo = trim($_POST["correo"] ?? "");
$password = $_POST["password"] ?? "";

if ($correo === "" || $password === "") {
    exit("Debes ingresar el correo y la contraseña.");
}

$sql = "SELECT id, nombre, correo, password, rol
        FROM usuarios
        WHERE correo = ?
        LIMIT 1";

$stmt = $conexion->prepare($sql);

if (!$stmt) {
    exit("Error al preparar la consulta.");
}

$stmt->bind_param("s", $correo);
if (!$stmt->execute()) {
    $stmt->close();
    exit("Error al ejecutar la consulta.");
}

$resultado = $stmt->get_result();

if (!$resultado) {
    $stmt->close();
    exit("Error al obtener el usuario.");
}

$usuario = $resultado->fetch_assoc();
$resultado->free();
$stmt->close();

if ($usuario && password_verify($password, $usuario["password"])) {
    session_regenerate_id(true);

    $_SESSION["usuario_id"] = $usuario["id"];
    $_SESSION["usuario_nombre"] = $usuario["nombre"];
    $_SESSION["usuario_correo"] = $usuario["correo"];

    $rol = strtolower(trim($usuario["rol"]));

    if (in_array($rol, ["admin", "administrador"], true)) {
        header("Location: admin_lobby.php");
        exit;
    }

    header("Location: lobby.php");
    exit;
}

$stmt->close();
$conexion->close();

header("Location: login.html?
error=credenciales");
?>
