-- DESTRUCTIVO: elimina todos los datos de ecotech_rrhh y reinicia los IDs.
-- Ejecutar solo si esta base está destinada exclusivamente a pruebas.
-- Requiere una cuenta administradora. La cuenta técnica ecotech_rrhh no basta.

USE ecotech_rrhh;
SELECT DATABASE() AS base_que_se_vaciara;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE password_reset_tokens;
TRUNCATE TABLE empleados_proyectos;
TRUNCATE TABLE registros_tiempo;
TRUNCATE TABLE indicadores;
TRUNCATE TABLE departamentos;
TRUNCATE TABLE proyectos;
TRUNCATE TABLE usuarios;
TRUNCATE TABLE empleados;
TRUNCATE TABLE roles;
SET FOREIGN_KEY_CHECKS = 1;
