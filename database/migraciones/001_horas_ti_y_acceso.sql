-- Aplicar en la BD existente con una cuenta administradora de MySQL.
-- No recrea tablas, no elimina registros y puede ejecutarse varias veces.
USE ecotech_rrhh;

-- El login comprueba también el estado del empleado, sin leer datos personales.
GRANT SELECT (id, activo) ON ecotech_rrhh.empleados TO 'ecotech_auth'@'%';

-- TI puede cargar, consultar y editar sus propias horas desde la aplicación.
GRANT SELECT ON ecotech_rrhh.proyectos TO 'ecotech_ti'@'%';
GRANT SELECT ON ecotech_rrhh.empleados_proyectos TO 'ecotech_ti'@'%';
GRANT SELECT, INSERT, UPDATE ON ecotech_rrhh.registros_tiempo TO 'ecotech_ti'@'%';

-- Los permisos se leen desde roles en cada login: actualizar solo el código
-- no cambia los roles ya almacenados. Conservar todos los permisos existentes.
START TRANSACTION;
UPDATE roles
SET permisos = JSON_ARRAY_APPEND(permisos, '$', 'registros.crear_propio')
WHERE perfil_bd = 'ti'
  AND NOT JSON_CONTAINS(permisos, JSON_QUOTE('registros.crear_propio'));
UPDATE roles
SET permisos = JSON_ARRAY_APPEND(permisos, '$', 'registros.leer_propios')
WHERE perfil_bd = 'ti'
  AND NOT JSON_CONTAINS(permisos, JSON_QUOTE('registros.leer_propios'));
UPDATE roles
SET permisos = JSON_ARRAY_APPEND(permisos, '$', 'registros.actualizar_propio')
WHERE perfil_bd = 'ti'
  AND NOT JSON_CONTAINS(permisos, JSON_QUOTE('registros.actualizar_propio'));
COMMIT;
