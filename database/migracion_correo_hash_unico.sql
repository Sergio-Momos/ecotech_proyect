-- Ejecutar como administrador SQL después de migracion_correo_hash_rellenar.py.
-- La tabla debe tener los hashes completados y sin duplicados.

USE ecotech_rrhh;

ALTER TABLE empleados
    MODIFY COLUMN correo_hash CHAR(64) NOT NULL,
    ADD UNIQUE INDEX uq_empleados_correo_hash (correo_hash);
