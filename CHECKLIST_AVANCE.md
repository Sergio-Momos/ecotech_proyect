# Checklist de avance EcoTech RRHH — evaluación práctica

Última revisión: **7 de octubre de 2026**.

Este checklist considera únicamente los diez criterios prácticos de la rúbrica: **G.1, G.2, G.5, G.6, G.9, G.10, G.13, G.14, G.17 y G.18**. Se excluyen los criterios orales.

- `[x]`: existe código o una verificación concreta que respalda el punto.
- `[ ]`: falta completar el punto o aportar evidencia para verificarlo.
- «Implementado» no equivale automáticamente al nivel «Excelente». La correspondencia exacta con el UML requiere el diagrama de referencia, que no fue proporcionado ni localizado en esta revisión.

## Resumen por criterio

| Criterio | Estado observado | Evidencia principal | Qué falta para cerrarlo |
| --- | --- | --- | --- |
| **2.1.1.G.1** — Clases, atributos, constructores y métodos | Clases implementadas; cotejo con UML pendiente | Nueve clases en `models/`; ocho tienen constructor explícito y `Seguridad` utiliza métodos estáticos | Comparar clases, firmas y atributos con el UML y los requerimientos originales |
| **2.1.1.G.2** — Relaciones del diseño | Relaciones representadas; cotejo con UML pendiente | Herencia, referencias entre objetos, colecciones y claves foráneas | Verificar multiplicidades y significado de composición/agregación; revisar el diseño de `Informe` y `Seguridad` |
| **2.1.2.G.5** — Encapsulamiento y herencia/abstracción | Implementado | Atributos internos, propiedades, colecciones de solo lectura y `Empleado(Persona)` | No se identifica un requisito adicional de abstracción sin consultar el UML |
| **2.1.2.G.6** — Consistencia y reutilización del modelo | Reutilización implementada; consistencia UML pendiente | `super().__init__()`, validaciones compartidas, modelos reutilizados por repositorios | Cotejar con el diseño original |
| **2.1.3.G.9** — Conexión con librería oficial | Implementado; conexión real verificada previamente | `mysql.connector`, `config.py`, perfiles y `database/conexion.py` | Repetir la comprobación en el equipo de entrega si cambia la configuración |
| **2.1.3.G.10** — CRUD ejecutado y verificado | CRUD implementado; verificación real completa pendiente | Operaciones en los seis repositorios; pruebas de horas con conexiones simuladas | Demostrar creación, consulta, modificación y eliminación/desactivación sobre MySQL real |
| **2.1.4.G.13** — Manejo de excepciones | Implementado parcialmente en la interfaz | Conexión, transacciones, login y gestión de horas tienen manejo de errores | Extender la captura de errores de MySQL/conexión a empleados, departamentos, proyectos y gestión de cuentas |
| **2.1.4.G.14** — Validación de entradas y continuidad | Validaciones implementadas; cobertura incompleta | Validaciones de modelos y formularios; 28 pruebas automatizadas | Rechazar salarios no finitos, reforzar referencias de `RegistroTiempo` y verificar errores en todas las pantallas |
| **2.1.5.G.17** — Análisis y pruebas de código apoyado por IA | Evidencia disponible | Fallos identificados y corregidos; 28 pruebas ejecutadas correctamente | Conservar y entregar las pruebas locales como evidencia |
| **2.1.5.G.18** — Adaptación y justificación del código apoyado por IA | Evidencia disponible para los cambios de esta conversación | Correcciones de login, permisos, lotes, validaciones y creación de usuarios; justificación técnica registrada abajo | Conservar estas evidencias junto con la entrega |

## 2.1.1.G.1 — Clases del modelo

Las clases no son archivos vacíos: todas cuentan con implementación.

| Listo | Clase | Atributos y comportamiento observados |
| --- | --- | --- |
| [x] | `Persona` | Constructor con id, nombre, dirección, teléfono, correo y RUT; propiedades con validación y `get_nombre_completo()` |
| [x] | `Empleado` | Hereda datos de `Persona`; salario, fecha de contrato, estado activo, proyectos, registros y usuario; registro de horas y creación de cuenta en memoria |
| [x] | `Departamento` | Constructor con id, nombre y gerente; colección de empleados; agregar, quitar, buscar y reasignar empleados |
| [x] | `Proyecto` | Constructor con id, nombre, descripción, fecha de inicio y estado; asignar/quitar empleados y activar/desactivar |
| [x] | `RegistroTiempo` | Fecha, horas, descripción, empleado y proyecto; id asignado al guardar; validación de fecha y horas |
| [x] | `Rol` | Nombre, perfil de BD y permisos; agregar/quitar/comprobar permisos y fábricas de RRHH, empleado y TI |
| [x] | `Usuario` | Constructor con id, username, contraseña, rol y estado; hash, verificación de contraseña, generación de username y reconstrucción desde BD |
| [x] | `Informe` | Tipo, fecha de generación, contenido y formato; generación desde filas de datos y exportación a PDF/Excel |
| [x] | `Seguridad` | Utilidad con métodos estáticos para hash de contraseña, verificación y hash de búsqueda; no define constructor propio |

- [ ] Confirmar que estas clases y sus firmas coinciden con el UML entregado al docente.
- [ ] Si el UML exige `Seguridad.cifrar_datos()` y `descifrar_datos()`, resolver esa diferencia: actualmente el cifrado está en el repositorio de empleados mediante MySQL, no en esos métodos del modelo.

## 2.1.1.G.2 — Relaciones del modelo

- [x] Herencia `Empleado → Persona`, declarada como `class Empleado(Persona)`.
- [x] Referencia `Usuario → Rol`, validada como instancia de `Rol`.
- [x] Dependencia `Usuario → Seguridad` para generar y verificar hashes.
- [x] Relación `Empleado — Usuario`: el empleado conserva `_usuario`; en SQL, el usuario comparte el id de su empleado y tiene una clave foránea con borrado en cascada.
- [x] Relación `Empleado — RegistroTiempo`: el empleado crea/conserva registros y cada registro referencia a su dueño; SQL conserva esa relación.
- [x] Relación `Departamento — Empleado` mediante colección de empleados y gerente; persistencia con `departamento_id` y `gerente_id`.
- [x] Asociación N:M `Empleado — Proyecto` mediante colecciones y la tabla `empleados_proyectos`.
- [x] `Proyecto.asignar_empleado()` y `quitar_empleado()` actualizan las colecciones de ambos objetos participantes.
- [x] Asociación `RegistroTiempo — Proyecto` mediante referencia y clave foránea.
- [ ] Confirmar las multiplicidades y las relaciones de composición/agregación frente al UML original.
- [ ] Verificar `Informe`: recibe `list[dict]` y no referencias directas a departamento, proyecto o registros. La casilla del checklist anterior sobre dependencias directas no queda confirmada por el código actual.

## 2.1.2.G.5 y G.6 — POO y reutilización

- [x] Atributos internos con prefijo `_` y acceso mediante propiedades en los modelos con estado.
- [x] Validaciones centralizadas en `utils/validaciones.py` y patrones/mensajes en `utils/constantes.py`.
- [x] Reutilización de los atributos y validaciones de `Persona` mediante `super().__init__()` en `Empleado`.
- [x] Colecciones expuestas como tuplas en empleado, departamento y proyecto; permisos expuestos como `frozenset` en rol.
- [x] Protección de ids frente a reasignaciones mediante setters; id de usuario sin setter público.
- [x] Contraseña sin lectura pública; escritura que valida y almacena un hash.
- [x] Reutilización de `RegistroTiempo` para carga de horas, edición y reconstrucción desde BD.
- [x] Regla semanal y de fecha duplicada compartida por el modelo de empleado y el repositorio de horas.
- [x] Separación en modelos, repositorios, conexión, interfaz y utilidades.
- [ ] Validar la consistencia completa de esa estructura con el UML original.

El prefijo `_` establece una convención de acceso interno en Python; no hace que los atributos sean inaccesibles. Las tuplas protegen la estructura de las colecciones, pero los objetos contenidos siguen siendo mutables. La rúbrica no exige añadir una clase abstracta si el problema no la necesita.

## 2.1.3.G.9 y G.10 — Conexión y CRUD

- [x] Uso de MySQL Connector/Python mediante `mysql.connector`.
- [x] Configuración local de host, puerto, usuario, contraseña y nombre de BD mediante `config.py` y variables de entorno.
- [x] Perfiles `auth`, `empleado`, `rrhh` y `ti`, seleccionados según la sesión.
- [x] Función `probar_conexion()` con `SELECT 1`.
- [x] Conexión real de los cuatro perfiles comprobada el **6 de octubre de 2026**. No se volvió a conectar a MySQL durante esta revisión.
- [x] Esquema persistente con tablas, claves foráneas y asociación N:M.
- [x] Parámetros `%s` para los datos introducidos en consultas SQL. El fragmento estructural del SELECT de empleados se construye a partir de cadenas internas.
- [x] Consultas que reconstruyen objetos del modelo.
- [x] Confirmación, reversión y cierre de recursos mediante `cursor_db()`.
- [x] Lotes de horas guardados en una sola transacción y validación del historial bajo bloqueo.

| Entidad | Registro | Consulta | Actualización | Eliminación o desactivación |
| --- | --- | --- | --- | --- |
| Empleados | `crear()` | Buscar/listar, con descifrado de datos | `actualizar()` | `eliminar()` realiza borrado lógico: `activo = FALSE` |
| Departamentos | `crear()` | Buscar/listar | `actualizar()`, asignar/quitar empleados | `eliminar()` realiza DELETE |
| Proyectos | `crear()` | Buscar/listar | `actualizar()`, asignar/quitar empleados, activar | `eliminar()` realiza borrado lógico |
| Registros de tiempo | `crear()`, `crear_lote()` | Buscar/listar y cargar historial | `actualizar()` | `eliminar()` realiza DELETE, con permiso de RRHH |
| Usuarios | `crear()`, `crear_para_empleado()` | Buscar/listar y buscar cuenta activa | Cambiar contraseña, activar/desactivar | Desactivación lógica |
| Roles | `crear()` | Buscar/listar | `actualizar()` | No se implementa eliminación de roles |

- [x] Migración de permisos y rol TI preparada en `database/migraciones/001_horas_ti_y_acceso.sql`.
- [ ] Confirmar la aplicación de esa migración sobre la BD existente; esta revisión no la ejecuta ni verifica su estado.
- [ ] Verificar un ciclo CRUD completo con datos de prueba en MySQL real, comprobando el resultado de cada operación.
- [ ] Probar el acceso y las operaciones permitidas de cada rol desde la interfaz.

Que existan consultas CRUD no demuestra por sí solo que se hayan ejecutado todas correctamente. Las pruebas locales de transacciones usan conexiones simuladas. El borrado lógico de empleados y proyectos está implementado y preserva los registros históricos; debe identificarse como desactivación en la demostración.

## 2.1.4.G.13 y G.14 — Excepciones y validaciones

- [x] Conversión de errores de conexión MySQL a `ConnectionError`.
- [x] Rollback ante fallos de una transacción; cierre de cursor y conexión en `finally`.
- [x] Captura de `ValueError`, `ConnectionError` y errores MySQL en el login.
- [x] Captura de errores de datos, permisos y BD en guardado de horas y otras acciones del módulo de registros.
- [x] Captura de `ValueError`/`TypeError` en formularios de empleados, departamentos, proyectos y creación/reseteo de cuentas.
- [x] Mensajes de error en pantalla y registros de auditoría.
- [x] Validación de nombre, texto no vacío, teléfono, correo y RUT chileno.
- [x] Validación de ids positivos y bloqueo de reasignación.
- [x] Validación de formato de username y requisitos de contraseña.
- [x] Salario numérico no negativo; fecha de contrato de tipo `date`.
- [x] Horas positivas, finitas, con máximo de dos decimales y hasta 10 horas por registro.
- [x] Fecha de registro no futura; un registro por empleado/día y hasta 42 horas por semana ISO.
- [x] Edición de horas que excluye su propio registro al recalcular el historial y verifica la pertenencia al empleado.
- [x] TI solo puede editar sus horas; el empleado estándar conserva creación y lectura propias.
- [x] Cargas masivas con rollback completo y sin ids asignados si falla la confirmación.
- [x] Edición fallida que conserva el objeto original.
- [x] Consulta de login que exige cuenta y empleado activos.

Pendientes observados:

- [ ] Capturar errores MySQL y `ConnectionError` en todos los flujos de empleados, departamentos, proyectos y cuentas; varias operaciones solo capturan errores de validación o no tienen captura.
- [ ] Rechazar salarios `NaN` e infinitos. Se confirmó localmente que `Empleado` acepta `float('nan')`.
- [ ] Validar explícitamente las referencias a empleado y proyecto en `RegistroTiempo`; el constructor y el setter de proyecto no comprueban sus tipos.
- [ ] Comprobar que formularios, navegación y listas gestionan errores sin dejar al usuario en un estado inconsistente.
- [ ] Realizar una prueba manual completa de las ventanas.

## 2.1.5.G.17 y G.18 — Revisión y adaptación de código apoyado por IA

Se registra únicamente el apoyo de IA observado en esta conversación; no se atribuye autoría al resto del proyecto.

- [x] Revisión del código para identificar errores concretos.
- [x] Adaptación del login para iniciar sesión una sola vez.
- [x] Corrección de la llamada a un generador de username inexistente.
- [x] Separación del permiso de edición propia de TI respecto de la edición general de RRHH.
- [x] Validación de edición contra el historial persistido, evitando fechas duplicadas y exceso semanal.
- [x] Cambio de inserciones independientes a un lote transaccional.
- [x] Bloqueo de acceso de empleados inactivos mediante la consulta de login.
- [x] Pruebas de regresión para errores, límites, permisos y rollback.
- [x] **28 pruebas automatizadas ejecutadas correctamente el 7 de octubre de 2026.**
- [x] **36 módulos Python revisados mediante compilación en memoria, sin errores de sintaxis.**

| Adaptación | Justificación técnica |
| --- | --- |
| Una llamada de inicio de sesión | Evita navegación y registros de auditoría repetidos |
| Permiso específico para editar horas propias | Habilita la necesidad de TI sin conceder edición general desde la aplicación |
| Validación del historial en el repositorio | No depende únicamente de botones o de información previamente cargada en memoria |
| Bloqueos y transacción para la carga masiva | Evitan cargas parciales y serializan las escrituras del mismo empleado |
| Asignación de ids después del commit | Permite reintentar un lote fallido sin dejar objetos con ids de registros no confirmados |
| Objeto separado para editar | Una validación o escritura fallida no altera el registro mostrado previamente |
| Uso de `generar_base_username()` en el modelo | Corrige la llamada a un método inexistente; la unicidad persistente se mantiene en el repositorio |
| Comprobar empleado activo en el login | Impide el ingreso con una cuenta activa perteneciente a un empleado desactivado |

Las pruebas están en `tests/test_horas.py` y `tests/test_flujos.py`. La carpeta `tests/` está excluida por `.gitignore`: existe localmente, pero no se incluirá automáticamente en una entrega basada solo en Git.

- [ ] Asegurar que la entrega incluya las pruebas que se utilizarán como evidencia de G.17.

## Funcionalidades adicionales ya implementadas

- [x] Interfaz CustomTkinter: login, dashboard, empleados, departamentos, proyectos, horas y gestión de cuentas TI.
- [x] Inicio y cierre de sesión en `app.py`; selección/limpieza del perfil de BD.
- [x] Punto de entrada de la aplicación gráfica: `app.py`.
- [x] Siembra de datos iniciales en `main.py`; no es el punto de entrada de la interfaz.
- [x] Hash de contraseñas con PBKDF2-HMAC-SHA256, salt aleatorio y comparación con `secrets.compare_digest()`.
- [x] Hash de búsqueda de RUT para comprobar unicidad.
- [x] Cifrado/descifrado de dirección, teléfono, correo, RUT y salario mediante `AES_ENCRYPT`/`AES_DECRYPT` en el repositorio de empleados.
- [x] Auditoría de acciones, errores y carga de horas mediante archivos de log con rotación.
- [x] Modelo `Informe` que admite filas de datos y exporta PDF/Excel.
- [ ] Conectar informes a la interfaz: actualmente no existe una pantalla que utilice `Informe`. --Lucy

## Pendientes prioritarios para la evaluación práctica

1. Cotejar el UML original con clases, atributos, métodos y relaciones; revisar especialmente `Informe` y la ubicación del cifrado.
2. Confirmar permisos/migración y demostrar CRUD completo en MySQL real.
3. Completar el manejo de errores de conexión y BD en las pantallas que aún no lo cubren.
4. Corregir las validaciones pendientes y verificar manualmente los formularios.
5. Incluir las pruebas locales y este checklist en la entrega.

La vista semanal, aprobación de períodos, alertas y nuevas funciones de gestión de horas no se consideran faltantes obligatorios de esta rúbrica por sí solas.
