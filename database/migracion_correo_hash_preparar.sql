-- Ejecutar una sola vez como administrador SQL en ecotech_rrhh.
-- Después ejecutar migracion_correo_hash_rellenar.py y, si termina bien,
-- ejecutar migracion_correo_hash_unico.sql.

USE ecotech_rrhh;

ALTER TABLE empleados
    ADD COLUMN correo_hash CHAR(64) NULL AFTER correo;
