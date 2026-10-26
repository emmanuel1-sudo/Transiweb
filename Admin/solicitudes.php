
<?php
require_once __DIR__ . "/../models/auth.php";
require_once __DIR__ . "/../models/conexion.php";

function e($valor) {
    return htmlspecialchars((string)$valor, ENT_QUOTES, "UTF-8");
}

$estados = [
    "pendiente" => "Pendiente",
    "en_proceso" => "En proceso",
    "aprobada" => "Aprobada",
    "rechazada" => "Rechazada"
];

$error = "";
$mensaje = "";

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $id = filter_input(INPUT_POST, "solicitud_id", FILTER_VALIDATE_INT);
    $estado = $_POST["estado"] ?? "";

    if (!$id || $id <= 0) {
        $error = "El ID de la solicitud no es válido.";
    } elseif (!array_key_exists($estado, $estados)) {
        $error = "El estado seleccionado no es válido.";
    } else {
        $stmt = $conexion->prepare(
            "UPDATE solicitudes SET estado = ? WHERE id = ?"
        );

        if (!$stmt) {
            $error = "No se pudo preparar la actualización.";
        } else {
            $stmt->bind_param("si", $estado, $id);

            if ($stmt->execute()) {
                $stmt->close();
                $conexion->close();

                header("Location: solicitudes.php?actualizada=1");
                exit;
            } else {
                $error = "No se pudo actualizar la solicitud.";
            }

            $stmt->close();
        }
    }
}

if (isset($_GET["actualizada"])) {
    $mensaje = "El estado de la solicitud se actualizó correctamente.";
}

$sql = "SELECT
            s.id,
            u.nombre AS usuario,
            u.correo,
            t.id AS tramite_id,
            s.estado,
            s.fecha_solicitud
        FROM solicitudes s
        INNER JOIN usuarios u ON s.usuario_id = u.id
        INNER JOIN tramites t ON s.tramite_id = t.id
        ORDER BY s.fecha_solicitud DESC";

$resultado = $conexion->query($sql);

if (!$resultado) {
    die("Error al consultar las solicitudes.");
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestionar solicitudes | Transiweb</title>
    
    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            padding: 30px 16px;
            font-family: Arial, sans-serif;
            background: #f2f5f9;
            color: #000000;
        }

        .contenedor {
            max-width: 1250px;
            margin: auto;
            padding: 25px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 18px rgba(0,0,0,.08);
        }

        .volver {
            display: inline-block;
            margin-bottom: 20px;
            color: #1769aa;
            text-decoration: none;
        }

        h1 { margin-top: 0; }

        .tabla-contenedor { overflow-x: auto; }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e1e6ed;
        }

        th {
            background: #1769aa;
            color: white;
        }

        select, button {
            padding: 9px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
            font-size: 14px;
        }

        button {
            margin-top: 6px;
            background: #1769aa;
            color: white;
            border: none;
            cursor: pointer;
        }

        button:hover { background: #105487; }

        .mensaje, .error {
            padding: 12px;
            border-radius: 6px;
            margin: 15px 0;
        }

        .mensaje {
            background: #e8f7ed;
            color: #176534;
        }

        .error {
            background: #fdecec;
            color: #a12626;
        }

        .vacio {
            padding: 20px 0;
            color: #667085;
        }
    </style>
</head>
<body>
<main class="contenedor">
    <a class="volver" href="../models/admin_lobby.php">← Volver al panel</a>

    <h1>Gestionar solicitudes</h1>
    <p>Solicitudes registradas: <?= $resultado->num_rows ?></p>

    <?php if ($mensaje !== ""): ?>
        <div class="mensaje"><?= e($mensaje) ?></div>
    <?php endif; ?>

    <?php if ($error !== ""): ?>
        <div class="error"><?= e($error) ?></div>
    <?php endif; ?>

    <?php if ($resultado->num_rows > 0): ?>
        <div class="tabla-contenedor">
            <table>
                <thead>
                <tr>
                    <th>ID</th>
                    <th>Usuario</th>
                    <th>Correo</th>
                    <th>ID del trámite</th>
                    <th>Estado actual</th>
                    <th>Fecha de solicitud</th>
                    <th>Actualizar estado</th>
                </tr>
                </thead>
                <tbody>
                <?php while ($fila = $resultado->fetch_assoc()): ?>
                    <tr>
                        <td><?= e($fila["id"]) ?></td>
                        <td><?= e($fila["usuario"]) ?></td>
                        <td><?= e($fila["correo"]) ?></td>
                        <td><?= e($fila["tramite_id"]) ?></td>
                        <td><?= e($estados[$fila["estado"]] ?? $fila["estado"]) ?></td>
                        <td><?= e($fila["fecha_solicitud"]) ?></td>
                        <td>
                            <form method="POST" action="solicitudes.php">
                                <input type="hidden" name="solicitud_id"
                                       value="<?= e($fila["id"]) ?>">

                                <select name="estado" required>
                                    <?php foreach ($estados as $valor => $etiqueta): ?>
                                        <option value="<?= e($valor) ?>"
                                            <?= $fila["estado"] === $valor ? "selected" : "" ?>>
                                            <?= e($etiqueta) ?>
                                        </option>
                                    <?php endforeach; ?>
                                </select>

                                <br>
                                <button type="submit">Guardar</button>
                            </form>
                        </td>
                    </tr>
                <?php endwhile; ?>
                </tbody>
            </table>
        </div>
    <?php else: ?>
        <p class="vacio">Todavía no hay solicitudes registradas.</p>
    <?php endif; ?>
</main>
</body>
</html>
<?php
$resultado->free();
$conexion->close();
?>
