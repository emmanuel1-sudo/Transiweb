
<?php
session_start();

// Verificar que exista una sesión iniciada
if (!isset($_SESSION["usuario_id"])) {
    header("Location: login.html");
    exit;
}

// Verificar que el usuario tenga rol de administrador
if (!isset($_SESSION["usuario_rol"]) ||
    $_SESSION["usuario_rol"] !== "admin") {
    http_response_code(403);
    exit("Acceso denegado. Solo el administrador puede entrar.");
}
?>
