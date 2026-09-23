from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

from models.empleado import Empleado
from models.rol import Rol
from repositorios import empleado_repo


class EmpleadoFormView(ctk.CTkToplevel):
    """Formulario modal para crear o editar un Empleado."""

    def __init__(self, parent, on_guardado, empleado_existente: Empleado | None = None):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self.empleado_existente = empleado_existente
        self.title("Editar empleado" if empleado_existente else "Nuevo empleado")
        self.geometry("380x520")
        self.grab_set()  # bloquea la ventana principal mientras esto está abierto

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
        try:
            fecha = datetime.strptime(self.entrada_fecha.get(), "%Y-%m-%d").date()
            salario = float(self.entradas["salario"].get())

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

        except (ValueError, TypeError) as e:
            messagebox.showerror("Datos inválidos", str(e))
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

        rol = self.app.usuario_actual.rol
        for empleado in empleado_repo.listar_todos():
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
        EmpleadoFormView(self, on_guardado=self._cargar_lista)

    def _abrir_formulario_editar(self, empleado: Empleado) -> None:
        EmpleadoFormView(self, on_guardado=self._cargar_lista, empleado_existente=empleado)

    def _desactivar(self, empleado: Empleado) -> None:
        if messagebox.askyesno("Confirmar", f"¿Desactivar a {empleado.nombre}?"):
            empleado_repo.eliminar(empleado.id)
            self._cargar_lista()


def _dashboard():
    from gui.dashboard_view import DashboardView
    return DashboardView