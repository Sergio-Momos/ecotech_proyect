from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

from models.empleado import Empleado
from models.rol import Rol
from repositorios import empleado_repo
from utils.auditoria import accion, error as log_error
from mysql.connector import Error as ErrorBD

class EmpleadoFormView(ctk.CTkToplevel):
    """Formulario modal para crear o editar un Empleado."""

    def __init__(self, parent, *, on_guardado, usuario_id, empleado_existente: Empleado | None = None):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self.empleado_existente = empleado_existente
        self.title("Editar empleado" if empleado_existente else "Nuevo empleado")
        self.geometry("380x680")
        self.grab_set()  # bloquea la ventana principal mientras esto está abierto
        self.usuario_id = usuario_id

        etiquetas_y_atributos = [
            ("Nombre", "nombre"), ("Dirección", "direccion"), ("Teléfono", "telefono"),
            ("Correo", "correo"), ("RUT", "rut"), ("Salario", "salario"),
        ]
        self.entradas = {}
        for etiqueta, atributo in etiquetas_y_atributos:
            ctk.CTkLabel(self, text=etiqueta).pack(pady=(12, 0))
            entrada = ctk.CTkEntry(self, width=280)
            if empleado_existente is not None:
                entrada.insert(0, str(getattr(empleado_existente, atributo)))
            entrada.pack()
            self.entradas[atributo] = entrada

        ctk.CTkLabel(self, text="Fecha inicio contrato (AAAA-MM-DD)").pack(pady=(12, 0))
        self.entrada_fecha = ctk.CTkEntry(self, width=280)
        if empleado_existente is not None:
            self.entrada_fecha.insert(0, empleado_existente.fecha_inicio_contrato.isoformat())
        self.entrada_fecha.pack()

        ctk.CTkButton(self, text="Guardar", command=self._guardar).pack(pady=25)

    def _guardar(self) -> None:
        accion_log = "CREAR_EMPLEADO" if self.empleado_existente is None else "ACTUALIZAR_EMPLEADO"
        try:
            try:
                fecha = datetime.strptime(self.entrada_fecha.get(), "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("La fecha debe tener el formato AAAA-MM-DD, por ejemplo 2026-10-09.") from None
            try:
                salario = float(self.entradas["salario"].get())
            except ValueError:
                raise ValueError("El salario debe ser un número, sin puntos ni símbolos. Ejemplo: 650000") from None

            if self.empleado_existente is None:
                nuevo = Empleado(
                    id=None,
                    nombre=self.entradas["nombre"].get(),
                    direccion=self.entradas["direccion"].get(),
                    telefono=self.entradas["telefono"].get(),
                    correo=self.entradas["correo"].get(),
                    rut=self.entradas["rut"].get(),
                    salario=salario,
                    fecha_inicio_contrato=fecha,
                )
                empleado_repo.crear(nuevo)
                accion(self.usuario_id, accion_log, f"empleado_id={nuevo.id}")
            else:
                emp = self.empleado_existente
                emp.nombre = self.entradas["nombre"].get()
                emp.direccion = self.entradas["direccion"].get()
                emp.telefono = self.entradas["telefono"].get()
                emp.correo = self.entradas["correo"].get()
                emp.rut = self.entradas["rut"].get()
                emp.salario = salario
                emp.fecha_inicio_contrato = fecha
                empleado_repo.actualizar(emp)
                accion(self.usuario_id, accion_log, f"empleado_id={emp.id}")

        except (ValueError, TypeError) as e:
            log_error(self.usuario_id, accion_log, str(e))
            messagebox.showerror("Datos inválidos", str(e))
            return
        except (ConnectionError, ErrorBD) as e:
            log_error(self.usuario_id, accion_log, str(e))
            messagebox.showerror("Error de base de datos", f"No se pudo guardar el empleado.\n{e}")
            return

        self.on_guardado()
        self.destroy()

class EmpleadosView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        rol = app.usuario_actual.rol

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(encabezado, text="← Volver", width=90,
                    command=lambda: app.navegar_a(_dashboard())).pack(side="left")
        ctk.CTkLabel(encabezado, text="Empleados", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)
        if rol.tiene_permiso(Rol.CREAR_EMPLEADOS):
            ctk.CTkButton(encabezado, text="+ Nuevo empleado",
                        command=self._abrir_formulario_crear).pack(side="right")

        self.lista = ctk.CTkScrollableFrame(self)
        self.lista.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._cargar_lista()

    def _cargar_lista(self) -> None:
        for widget in self.lista.winfo_children():
            widget.destroy()

        try:
            empleados = empleado_repo.listar_todos()
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("LISTAR_EMPLEADOS", "No se pudo cargar la lista de empleados.", e)
            return

        rol = self.app.usuario_actual.rol
        for empleado in empleados:
            fila = ctk.CTkFrame(self.lista)
            fila.pack(fill="x", pady=4)

            texto = f"{empleado.nombre}  ·  RUT {empleado.rut}  ·  ${empleado.salario:,.0f}"
            ctk.CTkLabel(fila, text=texto).pack(side="left", padx=10, pady=8)

            if rol.tiene_permiso(Rol.ELIMINAR_EMPLEADOS):
                ctk.CTkButton(
                    fila, text="Desactivar", width=90, fg_color="#B3261E",
                    command=lambda e=empleado: self._desactivar(e),
                ).pack(side="right", padx=6)

            if rol.tiene_permiso(Rol.CREAR_EMPLEADOS):
                ctk.CTkButton(
                    fila, text="Editar", width=90,
                    command=lambda e=empleado: self._abrir_formulario_editar(e),
                ).pack(side="right", padx=6)

    def _abrir_formulario_crear(self) -> None:
        EmpleadoFormView(self, on_guardado=self._cargar_lista,
                        usuario_id=self.app.usuario_actual.id)

    def _abrir_formulario_editar(self, empleado) -> None:
        EmpleadoFormView(self, on_guardado=self._cargar_lista,
                        usuario_id=self.app.usuario_actual.id,
                        empleado_existente=empleado)

    def _desactivar(self, empleado: Empleado) -> None:
        if not messagebox.askyesno("Confirmar", f"¿Desactivar a {empleado.nombre}?"):
            return
        try:
            empleado_repo.eliminar(empleado.id)
            accion(self.app.usuario_actual.id, "DESACTIVAR_EMPLEADO", f"empleado_id={empleado.id}")
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("DESACTIVAR_EMPLEADO", f"No se pudo desactivar a {empleado.nombre}.", e)
            return
        self._cargar_lista()

    def _error_bd(self, accion_log: str, mensaje: str, e: Exception) -> None:
        """Registra el error en logs/errores.log y se lo muestra al usuario."""
        log_error(self.app.usuario_actual.id, accion_log, str(e))
        messagebox.showerror("Error de base de datos", f"{mensaje}\n{e}")


def _dashboard():
    from gui.dashboard_view import DashboardView
    return DashboardView