-- Ejecutar una sola vez como root en la base ecotech_rrhh.
-- Habilita el vencimiento de contraseñas y códigos temporales de recuperación.

USE ecotech_rrhh;

ALTER TABLE usuarios
    ADD COLUMN password_changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE password_reset_tokens (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    empleado_id INT NOT NULL,
    token_hash CHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_password_reset_token (token_hash),
    INDEX idx_password_reset_empleado (empleado_id),
    CONSTRAINT fk_password_reset_empleado
        FOREIGN KEY (empleado_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Permisos mínimos adicionales para el flujo de recuperación.
-- La aplicación accede a esta cuenta usando su perfil auth.
GRANT SELECT ON ecotech_rrhh.empleados TO 'ecotech_auth'@'%';
GRANT UPDATE ON ecotech_rrhh.usuarios TO 'ecotech_auth'@'%';
GRANT SELECT, INSERT, UPDATE ON ecotech_rrhh.password_reset_tokens TO 'ecotech_auth'@'%';
