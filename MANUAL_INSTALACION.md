# Manual de instalación — EcoTech Solutions

**Sistema:** Gestión de Recursos Humanos (RRHH).

**Fecha de revisión:** 16 de octubre de 2026.

**Alcance:** instalación local desde el código fuente, para desarrollo o demostración.

## 1. Objetivo

Preparar Python y MySQL, configurar la conexión, cargar los datos iniciales y abrir la aplicación de escritorio. Al finalizar se podrá ingresar con los perfiles de Recursos Humanos, TI y Empleado.

La aplicación se ejecuta mediante `app.py`. El archivo `main.py` prepara los datos de ejemplo; no abre la interfaz. No requiere un servidor web ni se accede mediante una dirección en el navegador.

## 2. Requisitos previos

| Componente | Requisito |
| --- | --- |
| Python | 3.10 o superior por la sintaxis de tipos utilizada en el código. La revisión local se hizo con Python 3.14.8; no se verificaron todas las versiones intermedias. |
| Interfaz gráfica | Sesión de escritorio y Tkinter disponible en el Python elegido. |
| MySQL | Servidor instalado, iniciado y accesible; debe admitir columnas JSON y las funciones `AES_ENCRYPT` y `AES_DECRYPT`. |
| Cliente MySQL | Comando `mysql` o una herramienta como MySQL Workbench para ejecutar instrucciones SQL. |
| Acceso administrativo | Una cuenta MySQL que permita crear la base, las tablas, los usuarios técnicos y sus permisos. |
| Conexión a Internet | Necesaria para descargar las dependencias de Python si no están disponibles localmente. |
| Archivos del proyecto | Código fuente completo, incluido `database/esquema.sql`. |

Las instrucciones incluyen Windows y Linux. No se verificó una instalación completa en ambos sistemas.

## 3. Identificar los archivos principales

```text
ecotech_proyect/
├── app.py                 # Inicio de la aplicación de escritorio
├── main.py                # Carga de roles, empleados y usuarios de ejemplo
├── config.py              # Configuración local de la conexión
├── .env                   # Contraseñas y clave de cifrado locales
├── database/
│   ├── esquema.sql        # Creación de la base y sus siete tablas
│   └── conexion.py        # Conexiones con los cuatro perfiles técnicos
├── gui/                   # Ventanas y formularios
├── models/                # Entidades y reglas de validación
├── repositorios/          # Consultas y operaciones de base de datos
└── utils/                 # Validaciones, fechas y auditoría
```

**Antes de comenzar:** `config.py` y `.env` están excluidos de Git y pueden faltar en una copia descargada. Este manual explica cómo crearlos. El comentario inicial de `main.py` menciona `seed.py` y `database/roles_mysql.sql`, pero esos archivos no están presentes en la copia revisada: utilice `main.py` y las instrucciones SQL del apartado 7.

## 4. Abrir el proyecto y crear el entorno virtual

Abra una terminal dentro de la carpeta que contiene `app.py` y `main.py`. Si la ruta incluye espacios, escríbala entre comillas. Sustituya las rutas de ejemplo por la ubicación de su copia.

### Windows — Símbolo del sistema (CMD)

```bat
cd /d "C:\ruta\ecotech_proyect"
py --version
py -m venv .venv
.venv\Scripts\activate.bat
```

### Linux — Bash

```bash
cd "/ruta/ecotech_proyect"
python3 --version
python3 -m venv .venv
source .venv/bin/activate
```

Si ya existe una carpeta `.venv` de otra computadora, cree un entorno nuevo para su equipo; no reutilice ni copie ese entorno. Puede elegir otro nombre, por ejemplo `.venv-local`, y ajustar las rutas de activación.

Compruebe el intérprete activo:

```bash
python -c "import sys; print(sys.executable)"
```

La ruta debe apuntar al entorno recién creado. Mantenga ese entorno activo para los siguientes comandos de Python.

## 5. Instalar y comprobar las dependencias

La copia revisada no incluye `requirements.txt`. Instale los paquetes que importa el código:

```bash
python -m pip install customtkinter mysql-connector-python python-dotenv openpyxl reportlab
```

| Paquete | Uso en el proyecto |
| --- | --- |
| `customtkinter` | Interfaz de escritorio. |
| `mysql-connector-python` | Conexión y consultas MySQL. |
| `python-dotenv` | Lectura de la configuración desde `.env`. |
| `openpyxl` | Exportación de informes a Excel. |
| `reportlab` | Exportación de informes a PDF. |

Tkinter pertenece a la instalación de Python y no se instala con el comando anterior. Compruébelo con:

```bash
python -m tkinter
```

Debe abrirse una ventana de prueba; ciérrela para continuar. Si falta Tkinter o el módulo para crear entornos virtuales en Linux, instale los componentes correspondientes al Python y a la distribución que utiliza.

Verifique los demás módulos:

```bash
python -c "import customtkinter, mysql.connector, dotenv, openpyxl, reportlab; print('Dependencias disponibles')"
```

**Sobre el cifrado:** aunque el README anterior menciona Fernet y `cryptography`, el código actual cifra los campos de empleados mediante funciones AES de MySQL. No importa `cryptography`; ese paquete no es necesario para esta instalación.

## 6. Crear la base de datos

Inicie el servicio MySQL mediante las herramientas de su sistema. Después, desde la carpeta del proyecto, abra el cliente con una cuenta administradora:

```bash
mysql -u root -p
```

Ingrese la contraseña cuando se solicite. Si su administrador tiene otro nombre, sustituya `root`.

Dentro del cliente MySQL ejecute:

```sql
SOURCE database/esquema.sql;
USE ecotech_rrhh;
SHOW TABLES;
```

En Workbench, abra `database/esquema.sql` y ejecute el archivo completo. Deben aparecer estas siete tablas:

```text
departamentos
empleados
empleados_proyectos
proyectos
registros_tiempo
roles
usuarios
```

El esquema está pensado para una base nueva. Sus instrucciones `CREATE TABLE` no comprueban si cada tabla ya existe: no repita la importación sobre una instalación con datos. No necesita truncar tablas para instalar el sistema.

### 6.1. Adecuar las columnas que almacenan datos cifrados

El esquema entregado declara como `VARCHAR` cinco columnas donde `empleado_repo.py` guarda el resultado binario de `AES_ENCRYPT`. Para la base nueva, antes de cargar empleados, ejecute:

```sql
ALTER TABLE ecotech_rrhh.empleados
    MODIFY direccion BLOB NOT NULL,
    MODIFY telefono BLOB NOT NULL,
    MODIFY correo BLOB NOT NULL,
    MODIFY rut BLOB NOT NULL,
    MODIFY salario BLOB NOT NULL;
```

Este ajuste evita almacenar bytes cifrados como texto. MySQL indica que los resultados binarios de cifrado deben guardarse en columnas `VARBINARY` o `BLOB`; consulte la [documentación oficial de las funciones de cifrado](https://dev.mysql.com/doc/refman/8.4/en/encryption-functions.html). En una base que ya tiene información, respalde y revise los datos antes de aplicar cambios; convertir columnas no recupera valores que ya se hayan dañado.

## 7. Crear los usuarios técnicos de MySQL

Estos usuarios son cuentas de conexión a MySQL. Las personas ingresarán a la aplicación con otras credenciales, almacenadas en la tabla `usuarios`.

Ejecute el siguiente bloque con la cuenta administradora, en el cliente MySQL o en Workbench. **Reemplace primero las cuatro contraseñas de ejemplo por valores propios y distintos.** Guárdelas para configurar `.env`.

```sql
CREATE USER 'ecotech_auth'@'localhost'
    IDENTIFIED BY 'REEMPLAZAR_ClaveAuth#2026';
CREATE USER 'ecotech_empleado'@'localhost'
    IDENTIFIED BY 'REEMPLAZAR_ClaveEmpleado#2026';
CREATE USER 'ecotech_rrhh'@'localhost'
    IDENTIFIED BY 'REEMPLAZAR_ClaveRRHH#2026';
CREATE USER 'ecotech_ti'@'localhost'
    IDENTIFIED BY 'REEMPLAZAR_ClaveTI#2026';

-- Consultas previas al inicio de sesión.
GRANT SELECT ON ecotech_rrhh.usuarios TO 'ecotech_auth'@'localhost';
GRANT SELECT ON ecotech_rrhh.roles TO 'ecotech_auth'@'localhost';

-- Consultas necesarias para reconstruir empleados, proyectos e historiales.
GRANT SELECT ON ecotech_rrhh.* TO 'ecotech_empleado'@'localhost';
GRANT INSERT ON ecotech_rrhh.registros_tiempo TO 'ecotech_empleado'@'localhost';

-- Administración de RRHH.
GRANT SELECT ON ecotech_rrhh.* TO 'ecotech_rrhh'@'localhost';
GRANT INSERT, UPDATE ON ecotech_rrhh.empleados TO 'ecotech_rrhh'@'localhost';
GRANT INSERT, UPDATE, DELETE ON ecotech_rrhh.departamentos TO 'ecotech_rrhh'@'localhost';
GRANT INSERT, UPDATE ON ecotech_rrhh.proyectos TO 'ecotech_rrhh'@'localhost';
GRANT INSERT, DELETE ON ecotech_rrhh.empleados_proyectos TO 'ecotech_rrhh'@'localhost';
GRANT INSERT, UPDATE, DELETE ON ecotech_rrhh.registros_tiempo TO 'ecotech_rrhh'@'localhost';

-- Permisos adicionales de RRHH para cargar los datos iniciales con main.py.
GRANT INSERT, UPDATE ON ecotech_rrhh.roles TO 'ecotech_rrhh'@'localhost';
GRANT INSERT ON ecotech_rrhh.usuarios TO 'ecotech_rrhh'@'localhost';

-- Gestión de usuarios desde el perfil TI.
GRANT SELECT ON ecotech_rrhh.* TO 'ecotech_ti'@'localhost';
GRANT INSERT, UPDATE ON ecotech_rrhh.usuarios TO 'ecotech_ti'@'localhost';
```

Esta propuesta permite preparar una instalación local con las operaciones que realiza el código revisado. El perfil Empleado dispone de lectura sobre la base; la aplicación aplica los filtros de sus vistas. Estos permisos no implementan aislamiento por empleado dentro de MySQL.

Si las cuentas ya existen, revise sus permisos con `SHOW GRANTS FOR 'nombre'@'localhost';` y coordine sus credenciales antes de repetir el bloque. No elimine cuentas para resolver el error de usuario existente.

Los ejemplos suponen que MySQL está en la misma computadora que la aplicación. Para un servidor remoto, el administrador debe definir el origen permitido de las cuentas y la conexión correspondiente; las cuentas `@'localhost'` no cubren ese caso.

## 8. Configurar `.env` y `config.py`

### 8.1. Crear el archivo `.env`

En la raíz del proyecto, cree un archivo de texto llamado exactamente `.env`, sin extensión `.txt`. Si ya existe, edítelo conservando los valores necesarios; no lo reemplace sin revisar.

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ecotech_rrhh

DB_AUTH_USER=ecotech_auth
DB_AUTH_PASSWORD="REEMPLAZAR_ClaveAuth#2026"

DB_EMPLEADO_USER=ecotech_empleado
DB_EMPLEADO_PASSWORD="REEMPLAZAR_ClaveEmpleado#2026"

DB_RRHH_USER=ecotech_rrhh
DB_RRHH_PASSWORD="REEMPLAZAR_ClaveRRHH#2026"

DB_TI_USER=ecotech_ti
DB_TI_PASSWORD="REEMPLAZAR_ClaveTI#2026"

FERNET_KEY="REEMPLAZAR_POR_CLAVE_GENERADA"
```

Las contraseñas deben coincidir con las que configuró en MySQL. Ajuste el puerto si su servidor utiliza otro. Mantenga `DB_NAME=ecotech_rrhh` al seguir los bloques SQL de este manual.

Solo para una instalación nueva, genere una clave local:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copie el resultado en `FERNET_KEY`. El nombre de la variable se conserva por compatibilidad con `config.py`; su valor se entrega a MySQL como clave AES. **Si usa una base existente, necesita su clave original: no genere una nueva para esa base.** Conserve un respaldo de la clave junto con los respaldos de la base, con acceso restringido.

### 8.2. Comprobar o crear `config.py`

Si ya existe y define `DB_PROFILES` y `AES_KEY`, consérvelo y revise que lea las variables anteriores. Si falta, cree `config.py` junto a `app.py` con este contenido:

```python
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

DB_PROFILES = {
    perfil: {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get(f"DB_{sufijo}_USER", usuario),
        "password": os.environ.get(f"DB_{sufijo}_PASSWORD"),
        "database": os.environ.get("DB_NAME", "ecotech_rrhh"),
    }
    for perfil, sufijo, usuario in (
        ("auth", "AUTH", "ecotech_auth"),
        ("empleado", "EMPLEADO", "ecotech_empleado"),
        ("rrhh", "RRHH", "ecotech_rrhh"),
        ("ti", "TI", "ecotech_ti"),
    )
}

AES_KEY = os.environ.get("FERNET_KEY")
```

No publique `.env` ni archivos que contengan contraseñas reales. La copia revisada ya los excluye de Git mediante `.gitignore`.

## 9. Probar las cuatro conexiones

Desde la terminal, con el entorno virtual activo y situado en la raíz del proyecto:

```bash
python -c "from database.conexion import probar_conexion; [print(p, probar_conexion(p)) for p in ('auth', 'empleado', 'rrhh', 'ti')]"
```

El resultado esperado es:

```text
auth True
empleado True
rrhh True
ti True
```

Esta comprobación verifica acceso y `SELECT 1`; no comprueba todos los permisos de las tablas ni el descifrado de empleados. Si falla, corrija la conexión antes de cargar datos.

## 10. Cargar los datos iniciales

Para la base nueva, ejecute:

```bash
python main.py
```

El programa utiliza el perfil técnico `rrhh` y debe crear:

- Tres roles: Recursos Humanos, TI y Empleado.
- Cinco empleados y sus cuentas de acceso.
- Un departamento: `RecursosHumanos`.
- Un proyecto: `PanelesSolares`, con Ana Torres y Camila Rios asignadas.

Espere el mensaje **«Siembra completada»**. La consola muestra los nombres de usuario generados. En una base vacía, las credenciales de demostración son:

| Perfil | Usuario | Contraseña inicial |
| --- | --- | --- |
| Recursos Humanos | `a.principal` | `Admin#2024` |
| TI | `s.ti` | `TI#Clave2024` |
| Empleado — Ana Torres | `a.torres` | `Empleado#1` |
| Empleado — Juan Perez | `j.perez` | `Empleado#1` |
| Empleado — Camila Rios | `c.rios` | `Empleado#1` |

Los nombres pueden llevar un sufijo si existen colisiones; utilice los que indique la consola. Las cuentas ya existentes se conservan y sus contraseñas no se restablecen al repetir la carga.

La carga realiza varias operaciones independientes: un fallo puede dejar datos parciales. Además, la búsqueda de empleados excluye cuentas con rol TI, por lo que repetirla después de crear Soporte TI puede provocar un error de RUT duplicado. Si falla, revise lo creado antes de volver a ejecutarla; no vacíe las tablas como paso de recuperación automático.

Para confirmar el resultado en MySQL:

```sql
SELECT username, activo FROM ecotech_rrhh.usuarios ORDER BY id;
SELECT nombre, perfil_bd FROM ecotech_rrhh.roles ORDER BY id;
```

Al terminar la preparación, el administrador puede retirar los permisos temporales usados para sembrar roles y usuarios, si no volverá a ejecutar `main.py`:

```sql
REVOKE INSERT, UPDATE ON ecotech_rrhh.roles FROM 'ecotech_rrhh'@'localhost';
REVOKE INSERT ON ecotech_rrhh.usuarios FROM 'ecotech_rrhh'@'localhost';
```

Las contraseñas de demostración son públicas en el código. Antes de cargar datos reales, use la cuenta TI para restablecerlas desde **Gestión de usuarios**. La nueva contraseña debe tener al menos ocho caracteres, mayúscula, minúscula, número y un símbolo admitido por el sistema: `@ $ ! % * ? & #`.

## 11. Iniciar y verificar la aplicación

```bash
python app.py
```

Debe abrirse la ventana **«EcoTech Solutions — Gestión RRHH»**, con el formulario de inicio de sesión.

Realice estas comprobaciones en la base de demostración:

1. Ingrese como `a.principal` y abra empleados, departamentos, proyectos e informes.
2. Cierre la sesión e ingrese como `s.ti`; compruebe que aparece **Gestión de usuarios**.
3. Ingrese como `a.torres` y abra **Mis horas trabajadas**. Debe disponer del proyecto `PanelesSolares`.
4. Registre una jornada de prueba con fecha de hoy y una cantidad de horas permitida. Cierre y abra la aplicación para comprobar que el registro se conserva.
5. Desde RRHH, genere un informe de prueba en PDF o Excel y compruebe que se puede abrir.

La aplicación crea automáticamente `logs/acciones.log`, `logs/horas.log` y `logs/errores.log`. La cuenta del sistema operativo debe poder escribir en esa carpeta y en la ubicación elegida para los informes.

Para las siguientes ejecuciones, abra una terminal en el proyecto, active el entorno virtual y ejecute `python app.py`. No repita la creación de tablas ni la carga de ejemplo.

## 12. Solución de problemas

| Problema | Qué revisar |
| --- | --- |
| `python`, `py` o `mysql` no se reconoce | Compruebe que el componente está instalado y disponible en la terminal; puede usar la ruta completa de su ejecutable. |
| `ModuleNotFoundError` de una dependencia | Active el entorno correcto y repita la instalación del apartado 5 con `python -m pip`. |
| `No module named 'config'` | Cree `config.py` en la raíz del proyecto según el apartado 8.2. |
| Falta `_tkinter` o falla `python -m tkinter` | Instale el componente Tkinter de su distribución o habilite Tcl/Tk en su instalación de Python. |
| `no display name` o error de pantalla | Ejecute la aplicación desde una sesión gráfica de escritorio. |
| `Can't connect to MySQL server` | Compruebe que el servidor está iniciado y que host y puerto coinciden con `.env`. |
| `Access denied for user` | Revise usuario, contraseña, origen de la cuenta MySQL y sus permisos. |
| `Unknown database` o tabla inexistente | Compruebe que ejecutó el esquema en el servidor indicado y que `DB_NAME=ecotech_rrhh`. |
| Error al crear tablas existentes | Detenga la importación: el esquema es para una base nueva. Revise la instalación existente. |
| `Incorrect string value` al guardar empleados | Revise que aplicó el ajuste a columnas binarias del apartado 6.1. |
| Error de datos al cargar empleados o salario | Compruebe que `FERNET_KEY` es la clave original de esa base y que los valores cifrados se conservaron correctamente. |
| El inicio de sesión funciona pero un módulo falla | Pruebe el perfil MySQL del rol y revise sus permisos sobre las tablas utilizadas. |
| Usuario o contraseña incorrectos | Revise la salida de `main.py`; la cuenta debe estar activa. Repetir la carga no cambia una contraseña existente. |
| Error de RUT duplicado al repetir `main.py` | Revise los datos parciales y el caso de Soporte TI descrito en el apartado 10. |
| No puede escribir registros o exportaciones | Compruebe los permisos de escritura en `logs/` y en la carpeta de destino del informe. |

Para diagnosticar un fallo, conserve el mensaje de la terminal y consulte `logs/errores.log` si se generó. No comparta contraseñas ni la clave de cifrado al pedir soporte.

## 13. Lista de comprobación final

- [ ] Python y Tkinter funcionan en el entorno elegido.
- [ ] Las cinco dependencias de Python se importan correctamente.
- [ ] MySQL está iniciado y contiene las siete tablas.
- [ ] Las cinco columnas cifradas permiten almacenar datos binarios.
- [ ] Existen los cuatro usuarios técnicos y sus permisos.
- [ ] `.env` y `config.py` están completos; se conserva la clave de la base.
- [ ] Las cuatro pruebas de conexión devuelven `True`.
- [ ] `main.py` finaliza y se identifican las cuentas iniciales.
- [ ] `app.py` permite ingresar con los tres roles.
- [ ] Un registro de prueba persiste y se puede exportar un informe.

## 14. Alcance de la verificación de este manual

Los pasos se contrastaron con los archivos locales, sus importaciones, la configuración y las consultas de los repositorios. Se comprobó sin acceder a MySQL que los cinco empleados de ejemplo cumplen las validaciones del modelo y que los nombres base de usuario coinciden con la tabla del apartado 10.

No se creó ni modificó una base de datos durante la elaboración de este documento. Los bloques SQL, la carga completa y la navegación gráfica deben verificarse en la instalación de destino; no se presenta esta revisión como una prueba integral de instalación.
