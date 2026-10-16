<?php
session_start();

if (!isset($_SESSION["usuario_id"])) {
    header("Location: login.html");
    exit;
}

$nombre = htmlspecialchars(
    $_SESSION["usuario_nombre"],
    ENT_QUOTES,
    "UTF-8"
);
?>

<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Panel principal - Transiweb</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">

    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap"
        rel="stylesheet">

    <link rel="stylesheet" href="../vista/style/styles.css">
</head>

<body class="pagina-lobby">

    <header>
        <div class="wrap nav">

            <a href="../models/lobby.php" class="brand">
                <span class="dot"></span>
                TRANSIWEB
            </a>

            <a href="cerrar_sesion.php" class="nav-cta">
                Cerrar sesión
            </a>

        </div>
    </header>

    <main class="lobby-principal">

        <div class="wrap">

            <section class="lobby-bienvenida">

                <span class="section-eyebrow">
                    PANEL DE USUARIO
                </span>

                <h1>¡Bienvenido, <?php echo $nombre; ?>!</h1>

                <p>
                    Gestiona tus trámites de tránsito desde un solo lugar.
                </p>

            </section>

            <section class="lobby-grid">

                <a href="consultar_tramites.html#rutas" class="lobby-tarjeta">

                    <span class="lobby-icono">01</span>

                    <h2>Consultar trámites</h2>

                    <p>
                        Conoce los servicios disponibles en Transiweb.
                    </p>

                    <span class="lobby-enlace">
                        Ver trámites →
                    </span>

                </a>

                <a href="como_funciona.html#como" class="lobby-tarjeta">

                    <span class="lobby-icono">02</span>

                    <h2>Cómo funciona</h2>

                    <p>
                        Aprende los pasos para gestionar tus solicitudes.
                    </p>

                    <span class="lobby-enlace">
                        Conocer más →
                    </span>

                </a>

                <a href="consultar_tramites.html#contacto" class="lobby-tarjeta">

                    <span class="lobby-icono">03</span>

                    <h2>Ayuda y contacto</h2>

                    <p>
                        Encuentra información de contacto y soporte.
                    </p>

                    <span class="lobby-enlace">
                        Ver información →
                    </span>

                </a>

            </section>

            <div class="lobby-acciones">
                <a href="../models/index.html" class="btn-primary">
                    Volver a la página principal
                </a>
            </div>

        </div>

    </main>

    <footer>
        <div class="wrap">

            <div class="foot-bottom">
                <span>© 2026 Transiweb. Proyecto académico.</span>
                <span class="mono">v1.0 — lobby</span>
            </div>

        </div>
    </footer>

</body>
</html>