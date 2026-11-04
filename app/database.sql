CREATE DATABASE IF NOT EXISTS transiweb
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE transiweb;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    rol ENUM('usuario', 'admin') DEFAULT 'usuario',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tramites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS solicitudes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tramite_id INT NOT NULL,
    estado ENUM('pendiente', 'en_proceso', 'aprobada', 'rechazada')
        DEFAULT 'pendiente',
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (tramite_id) REFERENCES tramites(id)
);

INSERT INTO tramites (nombre, descripcion)
VALUES
('Licencia de conducción', 'Solicitud de licencia de conducción'),
('Matrícula vehicular', 'Trámite de matrícula de vehículos'),
('Renovación de licencia', 'Renovación de licencia de conducción');