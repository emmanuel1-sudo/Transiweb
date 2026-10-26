
<?php
require_once __DIR__ . "/../models/auth.php";
require_once __DIR__ . "/../models/conexion.php";

function e($valor) {
    return htmlspecialchars((string)$valor, ENT_QUOTES, "UTF-8");
}

$error = "";

// Obtener el ID del trámite
$id = filter_input(INPUT_GET, "id", FILTER_VALIDATE_INT);

if (!$id || $id <= 0) {
    header("Location: tramites.php");
    exit;
}

// Guardar los cambios
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $nombre = trim($_POST["nombre"] ?? "");
    $descripcion = trim($_POST["descripcion"] ?? "");
    $estado = $_POST["estado"] ?? "";

    if ($nombre === "") {
        $error = "Debes escribir el nombre del trámite.";
    } elseif (!in_array($estado, ["activo", "inactivo"], true)) {
        $error = "El estado seleccionado no es válido.";
    } else {
        $sql = "UPDATE tramites
                SET nombre = ?, descripcion = ?, estado = ?
                WHERE id = ?";

        $stmt = $conexion->prepare($sql);

        if (!$stmt) {
            $error = "No se pudo preparar la actualización.";
        } else {
            $stmt->bind_param(
                "sssi",
                $nombre,
                $descripcion,
                $estado,
                $id
            );

            if ($stmt->execute()) {
                $stmt->close();
                $conexion->close();

                header("Location: tramites.php?editado=1");
                exit;
            } else {
                $error = "No se pudieron guardar los cambios.";
            }

            $stmt->close();
        }
    }
}

// Consultar el trámite que se va a editar
$stmt = $conexion->prepare(
    "SELECT id, nombre, descripcion, estado
     FROM tramites
     WHERE id = ?"
);

if (!$stmt) {
    die("Error al consultar el trámite.");
}

$stmt->bind_param("i", $id);
$stmt->execute();

$resultado = $stmt->get_result();
$tramite = $resultado->fetch_assoc();

$resultado->free();
$stmt->close();

if (!$tramite) {
    $conexion->close();
    exit("No se encontró el trámite solicitado.");
}

// Si hubo un error, conservar lo escrito en el formulario
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $tramite["nombre"] = $_POST["nombre"] ?? $tramite["nombre"];
    $tramite["descripcion"] = $_POST["descripcion"] ?? $tramite["descripcion"];
    $tramite["estado"] = $_POST["estado"] ?? $tramite["estado"];
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar trámite | Transiweb</title>

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
            max-width: 650px;
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

        label {
            display: block;
            margin: 16px 0 7px;
            font-weight: bold;
        }

        input, textarea, select {
            width: 100%;
            padding: 11px;
            border: 1px solid #ccd5e0;
            border-radius: 6px;
            font: inherit;
        }

        textarea {
            min-height: 120px;
            resize: vertical;
        }

        button {
            margin-top: 20px;
            padding: 12px 18px;
            border: 0;
            border-radius: 6px;
            background: #227F87;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        .error {
            padding: 12px;
            margin: 15px 0;
            background: #fdeaea;
            color: #a32121;
            border-radius: 6px;
        }
    </style>
</head>

<body>
<main class="contenedor">

    <a class="volver" href="tramites.php">← Volver a trámites</a>

    <h1>Editar trámite #<?= e($tramite["id"]) ?></h1>

    <?php if ($error !== ""): ?>
        <div class="error"><?= e($error) ?></div>
    <?php endif; ?>

    <form method="POST" action="editar_tramite.php?id=<?= e($id) ?>">
        <label for="nombre">Nombre del trámite</label>
        <input
            type="text"
            id="nombre"
            name="nombre"
            maxlength="150"
            required
            value="<?= e($tramite["nombre"]) ?>"
        >

        <label for="descripcion">Descripción</label>
        <textarea
            id="descripcion"
            name="descripcion"
        ><?= e($tramite["descripcion"]) ?></textarea>

        <label for="estado">Estado</label>
        <select id="estado" name="estado" required>
            <option value="activo"
                <?= $tramite["estado"] === "activo" ? "selected" : "" ?>>
                Activo
            </option>
            <option value="inactivo"
                <?= $tramite["estado"] === "inactivo" ? "selected" : "" ?>>
                Inactivo
            </option>
        </select>

        <button type="submit">Guardar cambios</button>
    </form>

</main>
</body>
</html>

<?php
$conexion->close();
?>
