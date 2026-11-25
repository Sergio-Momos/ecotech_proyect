from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

from models.empleado import Empleado
from models.rol import Rol
from repositorios import empleado_repo
from gui.componentes import crear_encabezado, limpiar_contenedor
from utils.auditoria import accion, error as log_error
from utils.validaciones import validar_nombre_o_apellido
from mysql.connector import Error as ErrorBD

class EmpleadoFormView(ctk.CTkToplevel):
    """Formulario modal para crear o editar un Empleado."""

    def __init__(self, parent, *, on_guardado, usuario_id, empleado_existente: Empleado | None = None):
        super().__init__(parent)
        self._on_guardado = on_guardado
        self._empleado_existente = empleado_existente
        self.title("Editar empleado" if empleado_existente else "Nuevo empleado")
        self.geometry("380x740" if empleado_existente is None else "380x600")
        self.grab_set()  # bloquea la ventana principal mientras esto está abierto
        self._usuario_id = usuario_id

        if empleado_existente is None:
            etiquetas_y_atributos = [
                ("Primer nombre", "nombre"), ("Primer apellido", "apellido"),
            ]
        else:
            etiquetas_y_atributos = [("Nombre", "nombre")]
        etiquetas_y_atributos += [
            ("Dirección", "direccion"), ("Teléfono", "telefono"),
            ("Correo", "correo"),
        ]
        if empleado_existente is None:
            etiquetas_y_atributos.append(("RUT", "rut"))
        etiquetas_y_atributos.append(("Salario", "salario"))
        self._entradas = {}
        for etiqueta, atributo in etiquetas_y_atributos:
            ctk.CTkLabel(self, text=etiqueta).pack(pady=(12, 0))
            entrada = ctk.CTkEntry(self, width=280)
            if empleado_existente is not None:
                entrada.insert(0, str(getattr(empleado_existente, f"_{atributo}")))
            entrada.pack()
            self._entradas[atributo] = entrada

        if empleado_existente is None:
            ctk.CTkLabel(self, text="Fecha inicio contrato (AAAA-MM-DD)").pack(pady=(12, 0))
            self._entrada_fecha = ctk.CTkEntry(self, width=280)
            self._entrada_fecha.pack()

        ctk.CTkButton(self, text="Guardar", command=self._guardar).pack(pady=25)

    def _guardar(self) -> None:
        accion_log = "CREAR_EMPLEADO" if self._empleado_existente is None else "ACTUALIZAR_EMPLEADO"
        try:
            nombre = self._entradas["nombre"].get()
            if self._empleado_existente is None:
                nombre = validar_nombre_o_apellido(nombre, "El primer nombre")
                apellido = validar_nombre_o_apellido(
                    self._entradas["apellido"].get(), "El primer apellido"
                )
                # El modelo y la base de datos guardan el nombre completo en un solo campo.
                nombre = f"{nombre} {apellido}"
            fecha = None
            if self._empleado_existente is None:
                try:
                    fecha = datetime.strptime(self._entrada_fecha.get(), "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError("La fecha debe tener el formato AAAA-MM-DD, por ejemplo 2026-10-09.") from None
            try:
                salario = float(self._entradas["salario"].get())
            except ValueError:
                raise ValueError("El salario debe ser un número, sin puntos ni símbolos. Ejemplo: 650000") from None

            if self._empleado_existente is None:
                nuevo = Empleado(
                    id=None,
                    nombre=nombre,
                    direccion=self._entradas["direccion"].get(),
                    telefono=self._entradas["telefono"].get(),
                    correo=self._entradas["correo"].get(),
                    rut=self._entradas["rut"].get(),
                    salario=salario,
                    fecha_inicio_contrato=fecha,
                )
                empleado_repo.crear(nuevo)
                accion(self._usuario_id, accion_log, f"empleado_id={nuevo._id}")
            else:
                emp = self._empleado_existente
                emp._nombre = self._entradas["nombre"].get()
                emp._direccion = self._entradas["direccion"].get()
                emp._telefono = self._entradas["telefono"].get()
                emp._correo = self._entradas["correo"].get()
                emp._salario = salario
                empleado_repo.actualizar(emp)
                accion(self._usuario_id, accion_log, f"empleado_id={emp._id}")

        except (ValueError, TypeError) as e:
            log_error(self._usuario_id, accion_log, str(e))
            self._enfocar_campo_con_error(str(e))
            messagebox.showerror("Datos inválidos", str(e))
            return
        except (ConnectionError, ErrorBD) as e:
            log_error(self._usuario_id, accion_log, str(e))
            messagebox.showerror("Error de base de datos", f"No se pudo guardar el empleado.\n{e}")
            return

        self._on_guardado()
        self.destroy()

    def _enfocar_campo_con_error(self, mensaje: str) -> None:
        """Lleva el foco al campo que corresponde al mensaje de validación."""
        mensaje = mensaje.casefold()
        if "primer nombre" in mensaje:
            campo = "nombre"
        elif "primer apellido" in mensaje:
            campo = "apellido"
        elif "nombre" in mensaje:
            campo = "nombre"
        elif "dirección" in mensaje or "direccion" in mensaje:
            campo = "direccion"
        elif "teléfono" in mensaje or "telefono" in mensaje:
            campo = "telefono"
        elif "correo" in mensaje:
            campo = "correo"
        elif "rut" in mensaje:
            campo = "rut"
        elif "salario" in mensaje:
            campo = "salario"
        elif "fecha" in mensaje:
            self._entrada_fecha.focus_set()
            return
        else:
            return
        entrada = self._entradas.get(campo)
        if entrada is not None:
            entrada.focus_set()

class EmpleadosView(ctk.CTkFrame):
    """Lista empleados y ofrece acciones según los permisos del usuario."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self._mostrar_inactivos = False
        rol = app._usuario_actual._rol

        encabezado = crear_encabezado(self, app, "Empleados")
        if rol.tiene_permiso(Rol._CREAR_EMPLEADOS):
            ctk.CTkButton(encabezado, text="+ Nuevo empleado",
                        command=self._abrir_formulario_crear).pack(side="right")

        self._switch_inactivos = ctk.CTkSwitch(
            self, text="Mostrar empleados inactivos", command=self._toggle_inactivos
        )
        self._switch_inactivos.pack(anchor="w", padx=20, pady=(0, 8))

        self._lista = ctk.CTkScrollableFrame(self)
        self._lista.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._cargar_lista()

    def _toggle_inactivos(self) -> None:
        self._mostrar_inactivos = self._switch_inactivos.get() == 1
        self._cargar_lista()

    def _cargar_lista(self) -> None:
        limpiar_contenedor(self._lista)

        try:
            empleados = empleado_repo.listar_todos(incluir_inactivos=self._mostrar_inactivos)
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("LISTAR_EMPLEADOS", "No se pudo cargar la lista de empleados.", e)
            return

        rol = self._app._usuario_actual._rol
        for empleado in empleados:
            fila = ctk.CTkFrame(self._lista)
            fila.pack(fill="x", pady=4)

            estado = "  [INACTIVO]" if not empleado._activo else ""
            texto = f"{empleado._nombre}{estado}  ·  RUT {empleado._rut}  ·  ${empleado._salario:,.0f}"
            ctk.CTkLabel(fila, text=texto).pack(side="left", padx=10, pady=8)

            if rol.tiene_permiso(Rol._ELIMINAR_EMPLEADOS):
                if empleado._activo:
                    ctk.CTkButton(
                        fila, text="Desactivar", width=90, fg_color="#B3261E",
                        command=lambda e=empleado: self._desactivar(e),
                    ).pack(side="right", padx=6)
                else:
                    ctk.CTkButton(
                        fila, text="Reactivar", width=90,
                        command=lambda e=empleado: self._activar(e),
                    ).pack(side="right", padx=6)

            if rol.tiene_permiso(Rol._CREAR_EMPLEADOS):
                ctk.CTkButton(
                    fila, text="Editar", width=90,
                    command=lambda e=empleado: self._abrir_formulario_editar(e),
                ).pack(side="right", padx=6)

    def _abrir_formulario_crear(self) -> None:
        EmpleadoFormView(self, on_guardado=self._cargar_lista,
                        usuario_id=self._app._usuario_actual._id)

    def _abrir_formulario_editar(self, empleado) -> None:
        EmpleadoFormView(self, on_guardado=self._cargar_lista,
                        usuario_id=self._app._usuario_actual._id,
                        empleado_existente=empleado)

    def _desactivar(self, empleado: Empleado) -> None:
        if not messagebox.askyesno("Confirmar", f"¿Desactivar a {empleado._nombre}?"):
            return
        try:
            empleado_repo.eliminar(empleado._id)
            accion(self._app._usuario_actual._id, "DESACTIVAR_EMPLEADO", f"empleado_id={empleado._id}")
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("DESACTIVAR_EMPLEADO", f"No se pudo desactivar a {empleado._nombre}.", e)
            return
        self._cargar_lista()

    def _activar(self, empleado: Empleado) -> None:
        if not messagebox.askyesno("Confirmar", f"¿Reactivar a {empleado._nombre}?"):
            return
        try:
            empleado_repo.activar(empleado._id)
            accion(self._app._usuario_actual._id, "ACTIVAR_EMPLEADO", f"empleado_id={empleado._id}")
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("ACTIVAR_EMPLEADO", f"No se pudo reactivar a {empleado._nombre}.", e)
            return
        self._cargar_lista()

    def _error_bd(self, accion_log: str, mensaje: str, e: Exception) -> None:
        """Registra el error en logs/errores.log y se lo muestra al usuario."""
        log_error(self._app._usuario_actual._id, accion_log, str(e))
        messagebox.showerror("Error de base de datos", f"{mensaje}\n{e}")
