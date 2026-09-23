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
    departamento_id INT NULL
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
    permisos JSON NOT NULL
);

CREATE TABLE usuarios (
    id INT PRIMARY KEY,  -- mismo id que su Empleado dueño 
    username VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INT NOT NULL,
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