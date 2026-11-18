-- Ejecutar una sola vez en ecotech_rrhh para una base ya instalada.
-- Conserva el contenido actual de nombre; los apellidos existentes quedan
-- vacíos para que RRHH pueda completarlos desde la edición del empleado.

USE ecotech_rrhh;

ALTER TABLE empleados
    ADD COLUMN apellido VARCHAR(100) NOT NULL DEFAULT '' AFTER nombre;
