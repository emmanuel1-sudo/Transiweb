<?php
session_start();

if (!isset($_SESSION["usuario_id"])) {
    header("Location: ../models/login.html");
    exit;
}

require_once __DIR__ . "/../models/conexion.php";

// Comprobar el rol directamente en la base de datos
$id = $_SESSION["usuario_id"];

$sql = "SELECT nombre, rol FROM usuarios WHERE id = ? LIMIT 1";
$stmt = $conexion->prepare($sql);
$stmt->bind_param("i", $id);
$stmt->execute();

$resultado = $stmt->get_result();
$usuario = $resultado->fetch_assoc();
$stmt->close();

if (!$usuario) {
    header("Location: ../login.html");
    exit;
}

$rol = strtolower(trim($usuario["rol"]));

if (!in_array($rol, ["admin", "administrador"], true)) {
    header("Location: lobby.php");
    exit;
}

$nombre = htmlspecialchars($usuario["nombre"], ENT_QUOTES, "UTF-8");
?>

<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de administrador | Transiweb</title>
    <link rel="stylesheet" href="../vista/style/styles.css">

</head>

<body>
    <header class="site-header">
        <div class="container">
            <a href="../models/index.html" class="brand">TRANSIWEB</a>

            <a href="../models/cerrar_sesion.php" class="btn-primary">
                Cerrar sesión
            </a>
        </div>
    </header>

    <main class="admin-panel">

        <p class="admin-etiqueta">Panel de administración</p>

        <h1>¡Bienvenido, <?php echo htmlspecialchars($_SESSION["usuario_nombre"]); ?>!</h1>

        <p class="admin-descripcion">
            Administra los usuarios, supervisa las solicitudes y gestiona
            los trámites de Transiweb desde un solo lugar.
        </p>

        <section class="admin-grid">

            <article class="admin-tarjeta">
                <span class="admin-numero">01</span>
                <h2>Usuarios</h2>
                <p>Consulta y gestiona las cuentas registradas en Transiweb.</p>
                <a class="admin-enlace" href="usuarios.php">Gestionar usuarios →</a>
            </article>

            <article class="admin-tarjeta">
                <span class="admin-numero">02</span>
                <h2>Solicitudes</h2>
                <p>Supervisa las solicitudes y revisa sus estados actuales.</p>
                <a class="admin-enlace" href="solicitudes.php">Gestionar solicitudes →</a>
            </article>

            <article class="admin-tarjeta">
                <span class="admin-numero">03</span>
                <h2>Trámites</h2>
                <p>Accede a la sección de gestión de los trámites disponibles.</p>
                <a class="admin-enlace" href="tramites.php">Gestionar trámites →</a>
            </article>

        </section>

        <a class="admin-volver" href="../models/index.html">
            Volver a la página principal
        </a>

    </main>
</body>

</html>