
<?php
require_once __DIR__ . "/../models/auth.php";
require_once __DIR__ . "/../models/conexion.php";

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Verificar que el usuario conectado sea administrador
if (empty($_SESSION["usuario_id"])) {
    header("Location: ../login.php");
    exit;
}

$idAdministrador = (int) $_SESSION["usuario_id"];

$verificarAdmin = $conexion->prepare(
    "SELECT rol FROM usuarios WHERE id = ?"
);
$verificarAdmin->bind_param("i", $idAdministrador);
$verificarAdmin->execute();
$datosAdmin = $verificarAdmin->get_result()->fetch_assoc();
$verificarAdmin->close();

if (
    !$datosAdmin ||
    !in_array(strtolower($datosAdmin["rol"]), ["admin", "administrador"], true)
) {
    http_response_code(403);
    exit("Acceso denegado. Solo los administradores pueden gestionar usuarios.");
}

// Token de seguridad para los formularios
if (empty($_SESSION["csrf_usuarios"])) {
    $_SESSION["csrf_usuarios"] = bin2hex(random_bytes(32));
}

$tokenCSRF = $_SESSION["csrf_usuarios"];
$error = "";

// Procesar las operaciones
if ($_SERVER["REQUEST_METHOD"] === "POST") {

    $tokenRecibido = $_POST["csrf_token"] ?? "";

    if (!is_string($tokenRecibido) ||
        !hash_equals($tokenCSRF, $tokenRecibido)) {
        http_response_code(403);
        exit("Solicitud no válida. Recarga la página e inténtalo nuevamente.");
    }

    $accion = $_POST["accion"] ?? "";

    // EDITAR USUARIO
    if ($accion === "editar") {

        $id = filter_var($_POST["id"] ?? null, FILTER_VALIDATE_INT);
        $nombre = trim($_POST["nombre"] ?? "");
        $correo = trim($_POST["correo"] ?? "");
        $identificacion = trim($_POST["identificacion"] ?? "");
        $rol = strtolower(trim($_POST["rol"] ?? ""));

        $rolesPermitidos = [
            "admin",
            "administrador",
            "usuario",
            "ciudadano"
        ];

        if (!$id || $id < 1) {
            $error = "El ID del usuario no es válido.";
        } elseif (
            $nombre === "" ||
            $correo === "" ||
            $identificacion === ""
        ) {
            $error = "Todos los campos son obligatorios.";
        } elseif (!filter_var($correo, FILTER_VALIDATE_EMAIL)) {
            $error = "Ingresa un correo electrónico válido.";
        } elseif (!in_array($rol, $rolesPermitidos, true)) {
            $error = "El rol seleccionado no es válido.";
        } elseif ($id === $idAdministrador && $rol !== strtolower($datosAdmin["rol"])) {
            $error = "No puedes cambiar tu propio rol de administrador.";
        } else {

            // Comprobar si otro usuario ya tiene ese correo
            $consulta = $conexion->prepare(
                "SELECT id FROM usuarios
                 WHERE correo = ? AND id <> ?"
            );
            $consulta->bind_param("si", $correo, $id);
            $consulta->execute();
            $correoExiste = $consulta->get_result()->num_rows > 0;
            $consulta->close();

            // Comprobar si otro usuario tiene esa identificación
            $consulta = $conexion->prepare(
                "SELECT id FROM usuarios
                 WHERE identificacion = ? AND id <> ?"
            );
            $consulta->bind_param("si", $identificacion, $id);
            $consulta->execute();
            $identificacionExiste = $consulta->get_result()->num_rows > 0;
            $consulta->close();

            if ($correoExiste) {
                $error = "Ese correo ya está registrado por otro usuario.";
            } elseif ($identificacionExiste) {
                $error = "Esa identificación ya pertenece a otro usuario.";
            } else {

                $actualizar = $conexion->prepare(
                    "UPDATE usuarios
                     SET nombre = ?, correo = ?, identificacion = ?, rol = ?
                     WHERE id = ?"
                );

                $actualizar->bind_param(
                    "ssssi",
                    $nombre,
                    $correo,
                    $identificacion,
                    $rol,
                    $id
                );

                if ($actualizar->execute()) {
                    $actualizar->close();

                    header("Location: usuarios.php?mensaje=editado");
                    exit;
                }

                $actualizar->close();
                $error = "No fue posible actualizar el usuario.";
            }
        }
    }

    // ELIMINAR USUARIO
    elseif ($accion === "eliminar") {

        $id = filter_var($_POST["id"] ?? null, FILTER_VALIDATE_INT);

        if (!$id || $id < 1) {
            $error = "El ID del usuario no es válido.";
        } elseif ($id === 27 || $id === $idAdministrador) {
            $error = "No puedes eliminar la cuenta del administrador principal ni tu propia cuenta.";
        } else {

            $eliminar = $conexion->prepare(
                "DELETE FROM usuarios WHERE id = ?"
            );
            $eliminar->bind_param("i", $id);

            if ($eliminar->execute() && $eliminar->affected_rows > 0) {
                $eliminar->close();

                header("Location: usuarios.php?mensaje=eliminado");
                exit;
            }

            $eliminar->close();
            $error = "No se pudo eliminar el usuario. Comprueba que exista y que no tenga registros relacionados.";
        }
    }
}

// Mensajes después de completar una operación
$mensaje = "";

if (($_GET["mensaje"] ?? "") === "editado") {
    $mensaje = "Usuario actualizado correctamente.";
} elseif (($_GET["mensaje"] ?? "") === "eliminado") {
    $mensaje = "Usuario eliminado correctamente.";
}

// Buscar usuario que se va a editar
$usuarioEditar = null;
$idEditar = filter_input(INPUT_GET, "editar", FILTER_VALIDATE_INT);

if ($idEditar && $idEditar > 0) {
    $consulta = $conexion->prepare(
        "SELECT id, nombre, correo, identificacion, rol
         FROM usuarios WHERE id = ?"
    );
    $consulta->bind_param("i", $idEditar);
    $consulta->execute();
    $usuarioEditar = $consulta->get_result()->fetch_assoc();
    $consulta->close();

    if (!$usuarioEditar) {
        $error = "El usuario seleccionado no existe.";
    }
}

// Consultar todos los usuarios
$resultado = $conexion->query(
    "SELECT id, nombre, correo, identificacion, rol, fecha_registro
     FROM usuarios ORDER BY id DESC"
);

if (!$resultado) {
    die("Error al consultar los usuarios.");
}

function e($valor) {
    return htmlspecialchars((string) $valor, ENT_QUOTES, "UTF-8");
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestionar usuarios | Transiweb</title>

    <style>
        :root {
            --navy: #227F87;
            --navy2: #16223F;
            --amber: #FFB627;
            --paper: #F2F4F7;
            --white: #FFFFFF;
            --line: #E3E8EF;
            --red: #E63946;
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: var(--paper);
            color: var(--teal);
        }

        header {
            background: var(--navy);
            color: white;
            padding: 20px 5%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .marca {
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 1px;
        }

        .marca span { color: var(--white); }

        .etiqueta { color: var(--white); font-size: 13px; }

        main {
            max-width: 1250px;
            margin: 35px auto;
            padding: 0 20px;
        }

        .volver {
            display: inline-block;
            margin-bottom: 22px;
            color: var(--navy);
            text-decoration: none;
            font-weight: bold;
        }

        h1 { margin-bottom: 10px; }

        .subtitulo { color: #657187; line-height: 1.6; }

        .aviso {
            background: #E4F7E9;
            color: #176B3A;
            padding: 14px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .error {
            background: #FDE8E8;
            color: #A3212B;
            padding: 14px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .tarjeta {
            background: white;
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 22px;
            margin: 22px 0;
            box-shadow: 0 4px 18px #0000000D;
        }

        .total {
            border-left: 5px solid var(--amber);
            font-size: 18px;
            font-weight: bold;
        }

        .tabla-contenedor { overflow-x: auto; }

        table {
            width: 100%;
            min-width: 1050px;
            border-collapse: collapse;
        }

        th, td {
            padding: 13px;
            border-bottom: 1px solid var(--line);
            text-align: left;
            font-size: 14px;
        }

        th { background: var(--navy); color: white; }

        tbody tr:hover { background: #F8FAFC; }

        .rol {
            display: inline-block;
            background: #E9EEF5;
            padding: 6px 10px;
            border-radius: 20px;
            font-size: 12px;
        }

        .rol-admin { background: #FFF1C9; color: #795000; }

        .botones {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .boton {
            display: inline-block;
            border: 0;
            border-radius: 6px;
            padding: 9px 12px;
            text-decoration: none;
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
        }

        .editar { background: var(--navy); color: var(--white); }
        .eliminar { background: var(--red); color: white; }
        .cancelar { background: #E9EEF5; color: var(--navy); }

        label {
            display: block;
            margin: 14px 0 6px;
            font-weight: bold;
            font-size: 14px;
        }

        input, select {
            width: 100%;
            padding: 11px;
            border: 1px solid #CDD5E0;
            border-radius: 6px;
            font-size: 15px;
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0 18px;
        }

        .acciones-formulario {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 20px;
        }

        .vacio {
            text-align: center;
            padding: 25px;
            color: #657187;
        }

        footer {
            text-align: center;
            padding: 25px;
            color: #8D99AE;
            font-size: 13px;
        }

        @media (max-width: 600px) {
            main { padding: 0 12px; }
            .tarjeta { padding: 15px; }
            .form-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>

<body>

<header>
    <div class="marca">TRANSI<span>WEB</span></div>
    <div class="etiqueta">Panel administrativo</div>
</header>

<main>
    <a class="volver" href="../models/admin_lobby.php">
        &larr; Volver al panel
    </a>

    <h1>Gestionar usuarios</h1>
    <p class="subtitulo">
        Consulta, edita y elimina los usuarios registrados en Transiweb.
    </p>

    <?php if ($mensaje !== ""): ?>
        <div class="aviso" role="status"><?= e($mensaje) ?></div>
    <?php endif; ?>

    <?php if ($error !== ""): ?>
        <div class="error" role="alert"><?= e($error) ?></div>
    <?php endif; ?>

    <section class="tarjeta total">
        Usuarios registrados: <?= (int) $resultado->num_rows ?>
    </section>

    <?php if ($usuarioEditar): ?>
        <section class="tarjeta" id="formulario-edicion">
            <h2>Editar usuario #<?= (int) $usuarioEditar["id"] ?></h2>

            <form method="POST" action="usuarios.php">
                <input type="hidden" name="csrf_token"
                       value="<?= e($tokenCSRF) ?>">
                <input type="hidden" name="accion" value="editar">
                <input type="hidden" name="id"
                       value="<?= (int) $usuarioEditar["id"] ?>">

                <div class="form-grid">
                    <div>
                        <label for="nombre">Nombre completo</label>
                        <input id="nombre" name="nombre" type="text"
                               maxlength="150" required
                               value="<?= e($usuarioEditar["nombre"]) ?>">
                    </div>

                    <div>
                        <label for="correo">Correo electrónico</label>
                        <input id="correo" name="correo" type="email"
                               maxlength="254" required
                               value="<?= e($usuarioEditar["correo"]) ?>">
                    </div>

                    <div>
                        <label for="identificacion">Identificación</label>
                        <input id="identificacion" name="identificacion"
                               type="text" maxlength="50" required
                               value="<?= e($usuarioEditar["identificacion"]) ?>">
                    </div>

                    <div>
                        <label for="rol">Rol</label>
                        <select id="rol" name="rol" required
                            <?= (int) $usuarioEditar["id"] === $idAdministrador ? "disabled" : "" ?>>
                            <?php
                            $roles = [
                                "usuario" => "Usuario",
                                "ciudadano" => "Ciudadano",
                                "admin" => "Administrador",
                                "administrador" => "Administrador"
                            ];
                            foreach ($roles as $valor => $etiqueta):
                            ?>
                                <option value="<?= e($valor) ?>"
                                    <?= strtolower($usuarioEditar["rol"]) === $valor ? "selected" : "" ?>>
                                    <?= e($etiqueta) ?>
                                </option>
                            <?php endforeach; ?>
                        </select>

                        <?php if ((int) $usuarioEditar["id"] === $idAdministrador): ?>
                            <input type="hidden" name="rol"
                                   value="<?= e($usuarioEditar["rol"]) ?>">
                            <small>No puedes cambiar tu propio rol.</small>
                        <?php endif; ?>
                    </div>
                </div>

                <div class="acciones-formulario">
                    <button class="boton editar" type="submit">
                        Guardar cambios
                    </button>

                    <a class="boton cancelar" href="../Admin/usuarios.php">
                        Cancelar
                    </a>
                </div>
            </form>
        </section>
    <?php endif; ?>

    <section class="tarjeta">
        <h2>Listado de usuarios</h2>

        <div class="tabla-contenedor">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Nombre</th>
                        <th>Correo</th>
                        <th>Identificación</th>
                        <th>Rol</th>
                        <th>Fecha de registro</th>
                        <th>Acciones</th>
                    </tr>
                </thead>

                <tbody>
                <?php if ($resultado->num_rows > 0): ?>
                    <?php while ($fila = $resultado->fetch_assoc()): ?>
                        <tr>
                            <td><?= (int) $fila["id"] ?></td>
                            <td><?= e($fila["nombre"]) ?></td>
                            <td><?= e($fila["correo"]) ?></td>
                            <td><?= e($fila["identificacion"]) ?></td>
                            <td>
                                <span class="rol <?= in_array(strtolower($fila["rol"]), ["admin", "administrador"], true) ? "rol-admin" : "" ?>">
                                    <?= e($fila["rol"]) ?>
                                </span>
                            </td>
                            <td><?= e($fila["fecha_registro"]) ?></td>
                            <td>
                                <div class="botones">
                                    <a class="boton editar"
                                       href="../Admin/usuarios.php?editar=<?= (int) $fila["id"] ?>">
                                        Editar
                                    </a>

                                    <?php if ((int) $fila["id"] !== 27 && (int) $fila["id"] !== 28 &&
                                              (int) $fila["id"] !== $idAdministrador): ?>
                                        <form method="POST" action="../Admin/usuarios.php"
                                              onsubmit="return confirm('¿Seguro que deseas eliminar este usuario? Esta acción no se puede deshacer.');">
                                            <input type="hidden" name="csrf_token"
                                                   value="<?= e($tokenCSRF) ?>">
                                            <input type="hidden" name="accion"
                                                   value="eliminar">
                                            <input type="hidden" name="id"
                                                   value="<?= (int) $fila["id"] ?>">

                                            <button class="boton eliminar" type="submit">
                                                Eliminar
                                            </button>
                                        </form>
                                    <?php else: ?>
                                        <span title="Cuenta protegida">Protegido</span>
                                    <?php endif; ?>
                                </div>
                            </td>
                        </tr>
                    <?php endwhile; ?>
                <?php else: ?>
                    <tr>
                        <td colspan="7" class="vacio">
                            No hay usuarios registrados.
                        </td>
                    </tr>
                <?php endif; ?>
                </tbody>
            </table>
        </div>
    </section>
</main>

<footer>
    &copy; 2026 Transiweb. Proyecto académico.
</footer>

</body>
</html>

<?php
$resultado->free();
$conexion->close();
?>
