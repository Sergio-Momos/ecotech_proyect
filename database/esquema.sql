CREATE DATABASE IF NOT EXISTS ecotech_rrhh
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ecotech_rrhh;

CREATE TABLE empleados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(255) NOT NULL,
    telefono VARCHAR(255) NOT NULL,
    correo VARCHAR(255) NOT NULL,
    rut VARCHAR(255) NOT NULL,
    rut_hash CHAR(64) NOT NULL UNIQUE,   
    salario VARCHAR(255) NOT NULL,       
    fecha_inicio_contrato DATE NOT NULL,
    departamento_id INT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE departamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    gerente_id INT NOT NULL,
    FOREIGN KEY (gerente_id) REFERENCES empleados(id) ON DELETE RESTRICT
);

ALTER TABLE empleados
    ADD CONSTRAINT fk_empleado_departamento
    FOREIGN KEY (departamento_id) REFERENCES departamentos(id) ON DELETE SET NULL;

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    permisos JSON NOT NULL,
    perfil_bd VARCHAR(50) NOT NULL DEFAULT 'empleado'
);

CREATE TABLE usuarios (
    id INT PRIMARY KEY,  -- mismo id que su Empleado dueño 
    username VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (id) REFERENCES empleados(id) ON DELETE CASCADE,
    FOREIGN KEY (rol_id) REFERENCES roles(id)
);

CREATE TABLE proyectos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_inicio DATE NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE empleados_proyectos (
    empleado_id INT NOT NULL,
    proyecto_id INT NOT NULL,
    PRIMARY KEY (empleado_id, proyecto_id),
    FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
);

CREATE TABLE registros_tiempo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    horas_trabajadas DECIMAL(4,2) NOT NULL,
    descripcion TEXT NOT NULL,
    empleado_id INT NOT NULL,
    proyecto_id INT NOT NULL,
    FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE,
    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE RESTRICT
);

--Cambiar las secciones de contraseña por una segura de forma manual(revisar .env para ver que contraseñas tenemos por defecto)
CREATE USER IF NOT EXISTS 'ecotech_auth'@'%' IDENTIFIED BY '<contraseña_segura1>';
GRANT SELECT ON ecotech_rrhh.usuarios TO 'ecotech_auth'@'%';
GRANT SELECT ON ecotech_rrhh.roles TO 'ecotech_auth'@'%';
GRANT SELECT (id, activo) ON ecotech_rrhh.empleados TO 'ecotech_auth'@'%';

-- --- Cuenta para el Rol Empleado estándar ---
CREATE USER IF NOT EXISTS 'ecotech_empleado'@'%' IDENTIFIED BY '<contraseña_segura2>';
GRANT SELECT ON ecotech_rrhh.empleados TO 'ecotech_empleado'@'%';
GRANT SELECT ON ecotech_rrhh.proyectos TO 'ecotech_empleado'@'%';
GRANT SELECT, INSERT ON ecotech_rrhh.registros_tiempo TO 'ecotech_empleado'@'%';
-- Sin UPDATE ni DELETE acá a propósito: Rol.PERMISOS_EMPLEADO no incluye
-- actualizar_registros ni eliminar_registros — el privilegio SQL refleja
-- exactamente lo mismo que ya decide la capa de Python.

-- --- Cuenta para el Rol Recursos Humanos ---
CREATE USER IF NOT EXISTS 'ecotech_rrhh'@'%' IDENTIFIED BY '<contraseña_segura3>';
GRANT SELECT, INSERT, UPDATE, DELETE ON ecotech_rrhh.empleados TO 'ecotech_rrhh'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON ecotech_rrhh.departamentos TO 'ecotech_rrhh'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON ecotech_rrhh.proyectos TO 'ecotech_rrhh'@'%';
GRANT SELECT, INSERT, DELETE ON ecotech_rrhh.empleados_proyectos TO 'ecotech_rrhh'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON ecotech_rrhh.registros_tiempo TO 'ecotech_rrhh'@'%';
GRANT SELECT, INSERT, UPDATE ON ecotech_rrhh.roles TO 'ecotech_rrhh'@'%';
GRANT SELECT, INSERT ON ecotech_rrhh.usuarios TO 'ecotech_rrhh'@'%';
GRANT SELECT ON ecotech_rrhh.empleados_proyectos TO 'ecotech_empleado'@'%';
GRANT SELECT ON ecotech_rrhh.empleados TO 'ecotech_empleado'@'%';
-- Nota: ninguna cuenta recibe DROP, ALTER ni CREATE — eso es DDL,
-- exclusivo de la cuenta admin que corre este mismo script.


CREATE USER IF NOT EXISTS 'ecotech_ti'@'%' IDENTIFIED BY '<contrseña_segura_4>';
-- TI solo necesita ver empleados (para buscar a quién darle cuenta)
-- y gestionar usuarios y roles
GRANT SELECT ON ecotech_rrhh.empleados TO 'ecotech_ti'@'%';
GRANT SELECT ON ecotech_rrhh.roles TO 'ecotech_ti'@'%';
GRANT SELECT, INSERT, UPDATE ON ecotech_rrhh.usuarios TO 'ecotech_ti'@'%';
GRANT SELECT ON ecotech_rrhh.proyectos TO 'ecotech_ti'@'%';
GRANT SELECT ON ecotech_rrhh.empleados_proyectos TO 'ecotech_ti'@'%';
GRANT SELECT, INSERT, UPDATE ON ecotech_rrhh.registros_tiempo TO 'ecotech_ti'@'%';
-- La aplicación comprueba que TI solo edite registros de su propio empleado.

FLUSH PRIVILEGES;

--  Las columnas cifradas pasan de VARCHAR(255) a BLOB
--    (AES_ENCRYPT devuelve binario, no texto)
ALTER TABLE empleados
    MODIFY COLUMN direccion BLOB NOT NULL,
    MODIFY COLUMN telefono BLOB NOT NULL,
    MODIFY COLUMN correo BLOB NOT NULL,
    MODIFY COLUMN rut BLOB NOT NULL,
    MODIFY COLUMN salario BLOB NOT NULL;
