<?php
require_once __DIR__ . "/../models/auth.php";
require_once __DIR__ . "/../models/conexion.php";

$mensaje = "";
$error = "";


if (
    $_SERVER["REQUEST_METHOD"] === "POST" &&
    isset($_POST["eliminar_id"])
) {
    $id = filter_var(
        $_POST["eliminar_id"],
        FILTER_VALIDATE_INT
    );

    if ($id === false || $id === null || $id <= 0) {
        $error = "El ID del trámite no es válido.";
    } else {
        $stmt = $conexion->prepare(
            "DELETE FROM tramites WHERE id = ?"
        );

        if (!$stmt) {
            $error = "No se pudo preparar la eliminación.";
        } else {
            $stmt->bind_param("i", $id);

            if ($stmt->execute()) {
                if ($stmt->affected_rows > 0) {
                    $stmt->close();
                    $conexion->close();

                    header("Location: tramites.php?eliminado=1");
                    exit;
                } else {
                    $error = "No se encontró ese trámite.";
                }
            } else {
                $error = "No se pudo eliminar. Puede que el trámite tenga solicitudes asociadas.";
            }

            $stmt->close();
        }
    }
}

if (isset($_GET["eliminado"])) {
    $mensaje = "El trámite se eliminó correctamente.";
}


function e($valor)
{
    return htmlspecialchars((string)$valor, ENT_QUOTES, "UTF-8");
}

// Registrar un trámite nuevo
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $nombre = trim($_POST["nombre"] ?? "");
    $descripcion = trim($_POST["descripcion"] ?? "");

    if ($nombre === "") {
        $error = "Debes escribir el nombre del trámite.";
    } else {
        $sql = "INSERT INTO tramites (nombre, descripcion, estado)
                VALUES (?, ?, 'activo')";

        $stmt = $conexion->prepare($sql);

        if (!$stmt) {
            $error = "No se pudo preparar el registro del trámite.";
        } else {
            $stmt->bind_param("ss", $nombre, $descripcion);

            if ($stmt->execute()) {
                $stmt->close();
                $conexion->close();

                header("Location: tramites.php?creado=1");
                exit;
            } else {
                $error = "No se pudo registrar el trámite.";
            }

            $stmt->close();
        }
    }
}

if (isset($_GET["creado"])) {
    $mensaje = "El trámite se agregó correctamente.";
}

// Consultar trámites existentes
$sql = "SELECT id, nombre, descripcion, estado, creado_en
        FROM tramites
        ORDER BY id DESC";

$resultado = $conexion->query($sql);

if (!$resultado) {
    die("Error al consultar los trámites.");
}
?>
<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestionar trámites | Transiweb</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 30px 16px;
            font-family: Arial, sans-serif;
            background: #f2f5f9;
            color: #000000;
        }

        .contenedor {
            max-width: 1100px;
            margin: auto;
            padding: 25px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
        }

        .volver {
            display: inline-block;
            margin-bottom: 20px;
            color: #1769aa;
            text-decoration: none;
        }

        h1,
        h2 {
            margin-top: 0;
        }

        .formulario {
            margin: 25px 0;
            padding: 20px;
            background: #f7f9fc;
            border-radius: 10px;
        }

        label {
            display: block;
            margin: 15px 0 7px;
            font-weight: bold;
        }

        input,
        textarea {
            width: 100%;
            padding: 11px;
            border: 1px solid #ccd5e0;
            border-radius: 6px;
            font: inherit;
        }

        textarea {
            min-height: 100px;
            resize: vertical;
        }

        button {
            margin-top: 15px;
            padding: 11px 18px;
            border: 0;
            border-radius: 6px;
            background: #227F87;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            background: #125487;
        }

        .mensaje {
            padding: 12px;
            margin: 15px 0;
            background: #e7f7ec;
            color: #176534;
            border-radius: 6px;
        }

        .error {
            padding: 12px;
            margin: 15px 0;
            background: #fdeaea;
            color: #a32121;
            border-radius: 6px;
        }

        .tabla-contenedor {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th,
        td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e1e6ed;
            vertical-align: top;
        }

        th {
            background: #227F87;
            color: white;
        }

        .estado {
            font-weight: bold;
        }
    </style>
</head>

<body>
    <main class="contenedor">

        <a class="volver" href="../models/admin_lobby.php">
            ← Volver al panel
        </a>

        <h1>Gestionar trámites</h1>

        <?php if ($mensaje !== ""): ?>
            <div class="mensaje"><?= e($mensaje) ?></div>
        <?php endif; ?>

        <?php if ($error !== ""): ?>
            <div class="error"><?= e($error) ?></div>
        <?php endif; ?>

        <section class="formulario">
            <h2>Agregar un trámite</h2>

            <form method="POST" action="tramites.php">
                <label for="nombre">Nombre del trámite</label>
                <input
                    type="text"
                    id="nombre"
                    name="nombre"
                    maxlength="150"
                    required
                    value="<?= e($_POST["nombre"] ?? "") ?>">

                <label for="descripcion">Descripción</label>
                <textarea
                    id="descripcion"
                    name="descripcion"><?= e($_POST["descripcion"] ?? "") ?></textarea>

                <button type="submit">Agregar trámite</button>
            </form>
        </section>

        <h2>Trámites registrados</h2>
        <p>Total de trámites: <?= $resultado->num_rows ?></p>

        <div class="tabla-contenedor">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nombre</th>
                        <th>Descripción</th>
                        <th>Estado</th>
                        <th>Fecha de creación</th>
                        <th>Acciones</th>
                        </td>

                    </tr>
                </thead>

                <tbody>
                    <?php if ($resultado->num_rows > 0): ?>
                        <?php while ($fila = $resultado->fetch_assoc()): ?>
                            <tr>
                                <td><?= e($fila["id"]) ?></td>
                                <td><?= e($fila["nombre"]) ?></td>
                                <td><?= e($fila["descripcion"] ?? "") ?></td>
                                <td class="estado"><?= e($fila["estado"]) ?></td>
                                <td><?= e($fila["creado_en"]) ?></td>

                                <td>
                                    <form method="POST" action="tramites.php"
                                        onsubmit="return confirm('¿Estás seguro de que deseas eliminar este trámite? Esta acción no se puede deshacer.');">

                                        <input
                                            type="hidden"
                                            name="eliminar_id"
                                            value="<?= e($fila['id']) ?>">

                                        <button
                                            type="submit"
                                            style="background: #c62828;">
                                            Eliminar
                                        </button>
                                    </form>

                                    <a
                                        href="editar_tramite.php?id=<?= e($fila['id']) ?>"
                                        style="
        display: inline-block;
        margin-top: 8px;
        padding: 10px 14px;
        background: #227F87;
        color: white;
        text-decoration: none;
        border-radius: 6px;
    ">
                                        Editar
                                    </a>

                                </td>

                            </tr>
                        <?php endwhile; ?>
                    <?php else: ?>
                        <tr>
                            <td colspan="5">Todavía no hay trámites registrados.</td>
                        </tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>

    </main>
</body>

</html>

<?php
$resultado->free();
$conexion->close();
?>