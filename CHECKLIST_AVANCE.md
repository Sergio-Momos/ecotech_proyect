# Checklist de avance EcoTech RRHH

Última revisión: 17 de septiembre de 2026.

Este documento registra el estado observado directamente en el repositorio. Una casilla se marca solo cuando existe código para el requisito; las pruebas funcionales se registran por separado.

## Objetivo de la evaluación formativa

- [ ] Prototipo estructural completo que traduzca el UML validado a Python.
- [ ] Aplicación demostrable de encapsulamiento y reutilización mediante POO.
- [ ] Conexión exitosa a una base de datos desde el programa.

## Paso 1: Modelo UML en Python

### Clases solicitadas

- [x] `Persona`: atributos base, validaciones y `get_nombre_completo()`.
- [x] `Empleado`: hereda de `Persona`; incluye salario y fecha de inicio de contrato.
- [x] `Rol`: permisos encapsulados y método `tiene_permiso()`.
- [x] `Usuario`: Implementado sistema de validacion de contraseña Y HASHEO 
- [x] `Departamento`: archivo creado, sin implementación.
- [ ] `Proyecto`: archivo creado, sin implementación.
- [ ] `RegistroTiempo`: archivo creado, sin implementación.
- [ ] `Informe`: archivo creado, sin implementación.
- [x] `Seguridad`: PENDIENTE VER CIFRADO

### Relaciones y métodos del modelo

- [x] Herencia `Empleado` → `Persona`.
- [ ] Composición `Empleado` — `Usuario`.
- [ ] Composición `Empleado` — `RegistroTiempo`.
- [ ] Agregación `Departamento` — `Empleado`.
- [ ] Asociación N:M `Empleado` — `Proyecto`.
- [ ] Asociación `RegistroTiempo` — `Proyecto`.
- [ ] Asociación `Usuario` — `Rol`.
- [ ] Dependencia `Usuario` → `Seguridad`.
- [ ] Dependencias de `Informe` con departamento, proyecto y registros de tiempo.
- [ ] Métodos de gestión de `Departamento` y `Proyecto`.
- [ ] Autenticación de usuario y cierre de sesión.
- [ ] Generación y exportación de informes.

## Paso 2: Principios de programación orientada a objetos

- [x] Atributos internos con prefijo privado en `Persona`, `Empleado` y `Rol`.
- [x] Propiedades para validar y controlar el acceso a datos en `Persona` y `Empleado`.
- [x] Reutilización mediante herencia: `Empleado(Persona)`.
- [x] Validaciones reutilizables centralizadas en `utils/validaciones.py`.
- [x] Validación de RUT, correo, teléfono, nombre, salario y fecha de contrato.
- [ ] Encapsulamiento y validaciones aplicados al resto de las clases del modelo.
- [ ] Pruebas automatizadas de las validaciones y modelos.

## Paso 3: Base de datos

- [x] Estructura de carpeta `database/` creada.
- [ ] Configuración de la conexión en `database/conexion.py`.
- [ ] Esquema SQL con tablas persistentes en `database/esquema.sql`.
- [ ] Prueba de conexión exitosa desde Python con una librería oficial.
- [ ] Consultas parametrizadas para todas las operaciones SQL.
- [ ] Persistencia mediante repositorios.

## Arquitectura del proyecto

- [x] Carpetas creadas: `models/`, `repositorios/`, `database/`, `gui/` y `utils/`.
- [x] Repositorios previstos para empleado, departamento, proyecto y registro de tiempo.
- [x] Vistas previstas para login, empleados, departamentos, proyectos y registros.
- [ ] Implementación de repositorios.
- [ ] Implementación de interfaz Tkinter y punto de entrada en `main.py`.

## Seguridad

- [x] Validación de datos de entrada presente en el modelo inicial.
- [ ] Hash de contraseñas antes de almacenarlas.
- [ ] Verificación segura de contraseñas.
- [ ] Cifrado y descifrado de datos, si se mantiene en el diseño definitivo.
- [ ] SQL parametrizado en la capa de persistencia.

## Verificaciones realizadas

- [x] Compilación sintáctica de los módulos Python realizada correctamente el 17 de septiembre de 2026.
- [ ] Prueba de creación de objetos y comportamiento de cada modelo.
- [ ] Prueba de conexión y operaciones CRUD de base de datos.
- [ ] Prueba manual de las vistas de la interfaz.

## Próximo bloque recomendado

1. Implementar `Usuario` y `Seguridad` para dejar listo el acceso seguro.
2. Implementar `Departamento`, `Proyecto` y `RegistroTiempo`, incluyendo sus relaciones.
3. Crear el esquema SQLite y una prueba de conexión.
4. Implementar y probar un repositorio inicial, comenzando por empleados.
5. Conectar progresivamente las vistas Tkinter.

## Decisiones pendientes del diseño

- [ ] Confirmar si la autenticación será parte de `Usuario` o una clase separada.
- [ ] Definir las firmas finales de `verificar_password`, `cifrar_datos` y `descifrar_datos`.
- [ ] Mantener una única representación de cada relación: atributo de clase o relación gestionada por repositorio, evitando duplicación.
