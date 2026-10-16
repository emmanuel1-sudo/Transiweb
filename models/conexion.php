<?php
$servidor = "localhost";
$usuario = "root";
$password = "";
$base_datos = "transiweb";

$conexion = new mysqli($servidor,$usuario, $password, $base_datos);

if ($conexion -> connect_error) {
    die("Error de conexion: " . $conexion->connect_error);
}

$conexion -> set_charset("utf8");

?>