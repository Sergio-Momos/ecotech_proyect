import customtkinter as ctk
from tkinter import messagebox
from datetime import timedelta, datetime
from mysql.connector import Error as DatabaseError

from models.rol import Rol
from models.registro_tiempo import RegistroTiempo
from repositorios import empleado_repo, proyecto_repo, registro_tiempo_repo
from utils.auditoria import accion, registro_horas, error as log_error


class RegistroFormView(ctk.CTkToplevel):
    """Editar un registro con los permisos del usuario autenticado."""

    def __init__(self, parent, *, on_guardado, registro, usuario):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self.registro = registro
        self.usuario = usuario
        self.usuario_id = usuario.id
        self.title("Editar registro de horas")
        self.geometry("360x460")
        self.grab_set()

        ctk.CTkLabel(self, text=f"Empleado: {registro.empleado.nombre}", text_color="gray").pack(pady=(20, 10))

        ctk.CTkLabel(self, text="Fecha (AAAA-MM-DD)").pack(pady=(5, 0))
        self.entrada_fecha = ctk.CTkEntry(self, width=280)
        self.entrada_fecha.insert(0, registro.fecha.isoformat())
        self.entrada_fecha.pack()

        ctk.CTkLabel(self, text="Horas trabajadas").pack(pady=(15, 0))
        self.entrada_horas = ctk.CTkEntry(self, width=280)
        self.entrada_horas.insert(0, str(registro.horas_trabajadas))
        self.entrada_horas.pack()

        ctk.CTkLabel(self, text="Descripción").pack(pady=(15, 0))
        self.entrada_descripcion = ctk.CTkEntry(self, width=280)
        self.entrada_descripcion.insert(0, registro.descripcion)
        self.entrada_descripcion.pack()

        ctk.CTkLabel(self, text="Proyecto").pack(pady=(15, 0))
        proyectos = proyecto_repo.listar_todos()
        if not any(p.id == registro.proyecto.id for p in proyectos):
            proyectos.append(registro.proyecto)
        self._mapa_proyectos = {p.nombre: p for p in proyectos}
        self.selector_proyecto = ctk.CTkOptionMenu(
            self, values=list(self._mapa_proyectos.keys()), width=280
        )
        self.selector_proyecto.set(registro.proyecto.nombre)
        self.selector_proyecto.pack()

        ctk.CTkButton(self, text="Guardar", command=self._guardar).pack(pady=30)

    def _guardar(self) -> None:
        try:
            nuevo = RegistroTiempo(
                fecha=datetime.strptime(self.entrada_fecha.get(), "%Y-%m-%d").date(),
                horas_trabajadas=float(self.entrada_horas.get()),
                descripcion=self.entrada_descripcion.get(),
                empleado=self.registro.empleado,
                proyecto=self._mapa_proyectos[self.selector_proyecto.get()],
            )
            nuevo.id = self.registro.id
            registro_tiempo_repo.actualizar(nuevo, usuario=self.usuario)
            accion(self.usuario_id, "ACTUALIZAR_REGISTRO",
                   f"registro_id={nuevo.id}, empleado_id={nuevo.empleado.id}, "
                   f"fecha_anterior={self.registro.fecha}, fecha_nueva={nuevo.fecha}, "
                   f"horas_anteriores={self.registro.horas_trabajadas}, horas_nuevas={nuevo.horas_trabajadas}, "
                   f"proyecto_anterior={self.registro.proyecto.id}, proyecto_nuevo={nuevo.proyecto.id}")
        except (ValueError, TypeError, KeyError, PermissionError, ConnectionError, DatabaseError) as e:
            log_error(self.usuario_id, "ACTUALIZAR_REGISTRO", str(e))
            messagebox.showerror("Datos inválidos", str(e))
            return
        self.on_guardado()
        self.destroy()


class CargaMasivaView(ctk.CTkToplevel):
    """Genera una fila editable por cada día de un rango, y las guarda
    todas juntas — resuelve el caso de cargar muchas horas atrasadas
    sin perder la validación diaria/semanal por el camino."""

    def __init__(self, parent, *, empleado, on_guardado, usuario):
        super().__init__(parent)
        self.empleado = empleado
        self.on_guardado = on_guardado
        self.usuario = usuario
        self.usuario_id = usuario.id
        self.title("Carga masiva de horas")
        self.geometry("580x620")
        self.grab_set()

        proyectos = proyecto_repo.listar_todos()
        self._mapa_proyectos = {p.nombre: p for p in proyectos}

        controles = ctk.CTkFrame(self, fg_color="transparent")
        controles.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(controles, text="Proyecto").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 5))
        self.selector_proyecto = ctk.CTkOptionMenu(
            controles, values=list(self._mapa_proyectos.keys()) or ["(sin proyectos)"]
        )
        self.selector_proyecto.grid(row=1, column=0, columnspan=4, sticky="we", pady=(0, 10))

        ctk.CTkLabel(controles, text="Desde").grid(row=2, column=0, padx=(0, 5))
        self.entrada_desde = ctk.CTkEntry(controles, placeholder_text="AAAA-MM-DD", width=110)
        self.entrada_desde.grid(row=2, column=1, padx=(0, 15))

        ctk.CTkLabel(controles, text="Hasta").grid(row=2, column=2, padx=(0, 5))
        self.entrada_hasta = ctk.CTkEntry(controles, placeholder_text="AAAA-MM-DD", width=110)
        self.entrada_hasta.grid(row=2, column=3)

        ctk.CTkButton(self, text="Generar tabla", command=self._generar_filas).pack(pady=(0, 10))

        self.contenedor_filas = ctk.CTkScrollableFrame(
            self, label_text="Horas por día (deja en 0 los días no trabajados)"
        )
        self.contenedor_filas.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self._filas = []

        ctk.CTkButton(self, text="Guardar todo", command=self._guardar_lote).pack(pady=15)

    def _generar_filas(self) -> None:
        try:
            desde = datetime.strptime(self.entrada_desde.get(), "%Y-%m-%d").date()
            hasta = datetime.strptime(self.entrada_hasta.get(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Datos inválidos", "Las fechas deben tener formato AAAA-MM-DD.")
            return

        if hasta < desde:
            messagebox.showerror("Datos inválidos", "'Hasta' no puede ser anterior a 'Desde'.")
            return
        if (hasta - desde).days > 62:
            messagebox.showerror("Rango muy amplio", "Genera como máximo ~2 meses a la vez.")
            return

        for widget in self.contenedor_filas.winfo_children():
            widget.destroy()
        self._filas = []

        try:
            fechas_registradas = {
                r.fecha for r in registro_tiempo_repo.listar_por_empleado(self.empleado.id)
            }
        except (ConnectionError, DatabaseError) as e:
            log_error(self.usuario_id, "CONSULTAR_HORAS", str(e))
            messagebox.showerror("No se pudieron consultar las horas", str(e))
            return

        dia = desde
        while dia <= hasta:
            fila = ctk.CTkFrame(self.contenedor_filas)
            fila.pack(fill="x", pady=2)
            ctk.CTkLabel(fila, text=dia.isoformat(), width=100).pack(side="left", padx=5)
            entry_horas = ctk.CTkEntry(fila, width=60, placeholder_text="0")
            entry_horas.pack(side="left", padx=5)
            entry_descripcion = ctk.CTkEntry(fila, placeholder_text="Descripción")
            entry_descripcion.pack(side="left", padx=5, fill="x", expand=True)

            bloqueado = dia in fechas_registradas
            if bloqueado:
                entry_horas.configure(state="disabled")
                entry_descripcion.configure(state="disabled")
                ctk.CTkLabel(fila, text="Ya registrado").pack(side="right", padx=5)

            self._filas.append((dia, entry_horas, entry_descripcion, bloqueado))
            dia += timedelta(days=1)

    def _guardar_lote(self) -> None:
        if self.selector_proyecto.get() not in self._mapa_proyectos:
            messagebox.showerror("Datos inválidos", "Selecciona un proyecto válido.")
            return
        proyecto = self._mapa_proyectos[self.selector_proyecto.get()]

        if not self._filas:
            messagebox.showerror("Nada que guardar", "Genera la tabla primero.")
            return

        pendientes = []
        for dia, entry_horas, entry_descripcion, bloqueado in self._filas:
            if bloqueado:
                continue
            texto_horas = entry_horas.get().strip()
            if not texto_horas or texto_horas == "0":
                continue
            try:
                horas = float(texto_horas)
                registro = RegistroTiempo(
                    dia, horas, entry_descripcion.get() or "Carga masiva", self.empleado, proyecto
                )
            except (ValueError, TypeError) as e:
                messagebox.showerror("Error en el lote", f"Día {dia.isoformat()}: {e}")
                return
            pendientes.append(registro)

        if not pendientes:
            messagebox.showinfo("Nada que guardar", "No ingresaste horas en ninguna fila.")
            return

        try:
            registro_tiempo_repo.crear_lote(pendientes, usuario=self.usuario)
        except (ValueError, TypeError, PermissionError, ConnectionError, DatabaseError) as e:
            log_error(self.usuario_id, "CARGA_MASIVA_HORAS", str(e))
            messagebox.showerror("No se guardó el lote", str(e))
            return
        for registro in pendientes:
            registro_horas(self.usuario_id, self.empleado.id, proyecto.id,
                           str(registro.fecha), registro.horas_trabajadas)

        messagebox.showinfo("Listo", f"Se guardaron {len(pendientes)} registros.")
        self.on_guardado()
        self.destroy()


class RegistrosView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.rol = app.usuario_actual.rol
        self.empleado_actual = empleado_repo.buscar_por_id(app.usuario_actual.id)

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(encabezado, text="← Volver", width=90,
                      command=lambda: app.navegar_a(_dashboard())).pack(side="left")
        ctk.CTkLabel(encabezado, text="Registro de horas",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        if self.rol.tiene_permiso(Rol.LEER_REGISTROS_PROPIOS):
            self.tabs.add("Mis horas")
            self._construir_mis_horas(self.tabs.tab("Mis horas"))

        if self.rol.tiene_permiso(Rol.LEER_REGISTROS_TODOS):
            self.tabs.add("Todos los registros")
            self._construir_todos(self.tabs.tab("Todos los registros"))

    def _construir_mis_horas(self, contenedor) -> None:
        if self.rol.tiene_permiso(Rol.CREAR_REGISTRO_PROPIO):
            ctk.CTkButton(contenedor, text="Cargar horas (rango de fechas)",
                          command=self._abrir_carga_masiva).pack(anchor="w", pady=(10, 5))
        self.lista_mias = ctk.CTkScrollableFrame(contenedor)
        self.lista_mias.pack(fill="both", expand=True, pady=(5, 10))
        self._cargar_mis_registros()

    def _cargar_mis_registros(self) -> None:
        for widget in self.lista_mias.winfo_children():
            widget.destroy()
        for r in sorted(registro_tiempo_repo.listar_por_empleado(self.empleado_actual.id),
                        key=lambda x: x.fecha, reverse=True):
            fila = ctk.CTkFrame(self.lista_mias)
            fila.pack(fill="x", pady=2)
            ctk.CTkLabel(fila, text=f"{r.fecha}  ·  {r.horas_trabajadas}h  ·  "
                                    f"{r.proyecto.nombre}  ·  {r.descripcion}").pack(
                side="left", padx=10, pady=6)
            if (self.rol.tiene_permiso(Rol.ACTUALIZAR_REGISTRO_PROPIO)
                    or self.rol.tiene_permiso(Rol.ACTUALIZAR_REGISTROS)):
                ctk.CTkButton(fila, text="Editar", width=80,
                              command=lambda reg=r: self._editar(reg)).pack(side="right", padx=6)

    def _abrir_carga_masiva(self) -> None:
        CargaMasivaView(self, empleado=self.empleado_actual,
                        on_guardado=self._recargar_registros,
                        usuario=self.app.usuario_actual)

    def _construir_todos(self, contenedor) -> None:
        self.lista_todos = ctk.CTkScrollableFrame(contenedor)
        self.lista_todos.pack(fill="both", expand=True, pady=10)
        self._cargar_todos()

    def _cargar_todos(self) -> None:
        for widget in self.lista_todos.winfo_children():
            widget.destroy()
        for r in sorted(registro_tiempo_repo.listar_todos(),
                        key=lambda x: x.fecha, reverse=True):
            fila = ctk.CTkFrame(self.lista_todos)
            fila.pack(fill="x", pady=2)
            ctk.CTkLabel(fila, text=f"{r.fecha}  ·  {r.empleado.nombre}  ·  "
                                    f"{r.horas_trabajadas}h  ·  {r.proyecto.nombre}").pack(
                side="left", padx=10, pady=6)
            if self.rol.tiene_permiso(Rol.ELIMINAR_REGISTROS):
                ctk.CTkButton(fila, text="Eliminar", width=80, fg_color="#B3261E",
                              command=lambda reg=r: self._eliminar(reg)).pack(side="right", padx=6)
            if self.rol.tiene_permiso(Rol.ACTUALIZAR_REGISTROS):
                ctk.CTkButton(fila, text="Editar", width=80,
                              command=lambda reg=r: self._editar(reg)).pack(side="right", padx=6)

    def _editar(self, registro) -> None:
        try:
            RegistroFormView(self, on_guardado=self._recargar_registros,
                             registro=registro, usuario=self.app.usuario_actual)
        except (ValueError, ConnectionError, DatabaseError) as e:
            log_error(self.app.usuario_actual.id, "ABRIR_EDICION_HORAS", str(e))
            messagebox.showerror("No se pudo abrir el registro", str(e))

    def _recargar_registros(self) -> None:
        if hasattr(self, "lista_mias"):
            self._cargar_mis_registros()
        if hasattr(self, "lista_todos"):
            self._cargar_todos()

    def _eliminar(self, registro) -> None:
        if messagebox.askyesno("Confirmar", f"¿Eliminar el registro del {registro.fecha}?"):
            try:
                registro_tiempo_repo.eliminar(registro.id, usuario=self.app.usuario_actual)
            except (PermissionError, ConnectionError, DatabaseError) as e:
                log_error(self.app.usuario_actual.id, "ELIMINAR_REGISTRO", str(e))
                messagebox.showerror("No se pudo eliminar el registro", str(e))
                return
            accion(self.app.usuario_actual.id, "ELIMINAR_REGISTRO",
                   f"registro_id={registro.id}, empleado_id={registro.empleado.id}")
            self._recargar_registros()


def _dashboard():
    from gui.dashboard_view import DashboardView
    return DashboardView
