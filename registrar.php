<?php

require_once "conexion.php";

if ($_SERVER["REQUEST_METHOD"] !== "POST") {
    header("Location: registro.html");
    exit;
}

// Recibir los datos del formulario
$nombre = trim($_POST["nombre"] ?? "");
$correo = trim($_POST["correo"] ?? "");
$identificacion = trim($_POST["identificacion"] ?? "");
$password = $_POST["password"] ?? "";

// Validar los campos
if ($nombre === "" || $correo === "" ||
    $identificacion === "" || $password === "") {

    exit("Todos los campos son obligatorios. <a href='registro.html'>Volver</a>");
}

if (!filter_var($correo, FILTER_VALIDATE_EMAIL)) {
    exit("El correo electrónico no es válido. <a href='registro.html'>Volver</a>");
}

// Encriptar la contraseña
$password_segura = password_hash($password, PASSWORD_DEFAULT);

// Preparar el registro
$sql = "INSERT INTO usuarios
        (nombre, correo, identificacion, password)
        VALUES (?, ?, ?, ?)";

$stmt = $conexion->prepare($sql);

if (!$stmt) {
    exit("Error al preparar el registro.");
}

$stmt->bind_param(
    "ssss",
    $nombre,
    $correo,
    $identificacion,
    $password_segura
);

mysqli_report(MYSQLI_REPORT_OFF);

// Guardar el usuario
if ($stmt->execute()) {

    echo '
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Registro exitoso - Transiweb</title>
        <link rel="stylesheet" href="styles.css">
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

                <a href="login.html" class="btn-primary">
                    Iniciar sesión
                </a>

            </div>
        </main>

    </body>
    </html>';

} elseif ($stmt->errno === 1062) {

    echo '
    <div class="tarjeta-mensaje">
        <h2>Usuario ya registrado</h2>
        <p>El correo o la identificación ya existen.</p>
        <a href="registro.html" class="btn-primary">Volver al registro</a>
    </div>';

} else {

    echo "No se pudo registrar la cuenta. Verifica la tabla usuarios.";

}

$stmt->close();
$conexion->close();

?>