import customtkinter as ctk
from tkinter import messagebox
from datetime import timedelta, datetime
 
from models.rol import Rol
from repositorios import empleado_repo, proyecto_repo, registro_tiempo_repo
from utils.auditoria import accion, registro_horas, error as log_error
from mysql.connector import Error as ErrorBD
 
 
class RegistroFormView(ctk.CTkToplevel):
 
    def __init__(self, parent, *, on_guardado, registro, usuario_id: int):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self.registro = registro
        self.usuario_id = usuario_id
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
        self._mapa_proyectos = {p.nombre: p for p in proyectos}
        self.selector_proyecto = ctk.CTkOptionMenu(
            self, values=list(self._mapa_proyectos.keys()), width=280
        )
        self.selector_proyecto.set(registro.proyecto.nombre)
        self.selector_proyecto.pack()
 
        ctk.CTkButton(self, text="Guardar", command=self._guardar).pack(pady=30)
 
    def _guardar(self) -> None:
        try:
            self.registro.fecha = datetime.strptime(self.entrada_fecha.get(), "%Y-%m-%d").date()
            self.registro.horas_trabajadas = float(self.entrada_horas.get())
            self.registro.descripcion = self.entrada_descripcion.get()
            self.registro.proyecto = self._mapa_proyectos[self.selector_proyecto.get()]
            registro_tiempo_repo.actualizar(self.registro)
            accion(self.usuario_id, "ACTUALIZAR_REGISTRO",
                   f"registro_id={self.registro.id}, empleado_id={self.registro.empleado.id}")
        except (ValueError, TypeError, KeyError) as e:
            log_error(self.usuario_id, "ACTUALIZAR_REGISTRO", str(e))
            messagebox.showerror("Datos inválidos", str(e))
            return
        except (ConnectionError, ErrorBD) as e:
            log_error(self.usuario_id, "ACTUALIZAR_REGISTRO", str(e))
            messagebox.showerror("Error de base de datos", f"No se pudo guardar el registro.\n{e}")
            return
        self.on_guardado()
        self.destroy()
 
 
class CargaMasivaView(ctk.CTkToplevel):
 
    def __init__(self, parent, *, empleado, on_guardado, usuario_id: int):
        super().__init__(parent)
        self.empleado = empleado
        self.on_guardado = on_guardado
        self.usuario_id = usuario_id
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
 
    def _error_bd(self, mensaje: str, e: Exception) -> None:
        log_error(self.usuario_id, "CARGA_MASIVA", str(e))
        messagebox.showerror("Error de base de datos", f"{mensaje}\n{e}")
 
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
 
        try:
            fechas_registradas = {
                r.fecha for r in registro_tiempo_repo.listar_por_empleado(self.empleado.id)
            }
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("No se pudieron revisar los días ya registrados.", e)
            return
 
        for widget in self.contenedor_filas.winfo_children():
            widget.destroy()
        self._filas = []
 
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
 
        try:
            registro_tiempo_repo.cargar_historial(self.empleado)
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("No se pudo revisar tu historial de horas.", e)
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
                registro = self.empleado.registrar_horas(
                    dia, horas, entry_descripcion.get() or "Carga masiva", proyecto
                )
            except (ValueError, TypeError) as e:
                messagebox.showerror("Error en el lote", f"Día {dia.isoformat()}: {e}")
                return
            pendientes.append(registro)
 
        if not pendientes:
            messagebox.showinfo("Nada que guardar", "No ingresaste horas en ninguna fila.")
            return
 
        guardados = 0
        try:
            for registro in pendientes:
                registro_tiempo_repo.crear(registro)
                registro_horas(self.usuario_id, self.empleado.id, proyecto.id,
                               str(registro.fecha), registro.horas_trabajadas)
                guardados += 1
        except (ConnectionError, ErrorBD) as e:
            self._error_bd(f"Se guardaron {guardados} de {len(pendientes)} registros antes del error.", e)
            self.on_guardado()
            return
 
        messagebox.showinfo("Listo", f"Se guardaron {len(pendientes)} registros.")
        self.on_guardado()
        self.destroy()
 
 
class RegistrosView(ctk.CTkFrame):
    TODOS = "(Todos)"
 
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
            self._construir_mis_horas(self.tabs.add("Mis horas"))
        if self.rol.tiene_permiso(Rol.LEER_REGISTROS_TODOS):
            self._construir_todos(self.tabs.add("Todos los registros"))
 
    def _error_bd(self, accion_log: str, mensaje: str, e: Exception) -> None:
        log_error(self.app.usuario_actual.id, accion_log, str(e))
        messagebox.showerror("Error de base de datos", f"{mensaje}\n{e}")
 
    def _mostrar(self, lista, registros, con_empleado: bool) -> None:
        for widget in lista.winfo_children():
            widget.destroy()
        if not registros:
            ctk.CTkLabel(lista, text="No hay registros.", text_color="gray").pack(pady=20)
            return
        for r in registros:
            fila = ctk.CTkFrame(lista)
            fila.pack(fill="x", pady=2)
            empleado = f"{r.empleado.nombre}  ·  " if con_empleado else ""
            ctk.CTkLabel(fila, text=f"{r.fecha}  ·  {empleado}{r.horas_trabajadas}h  ·  "
                                    f"{r.proyecto.nombre}  ·  {r.descripcion}").pack(
                side="left", padx=10, pady=6)
            if not con_empleado:
                continue
            if self.rol.tiene_permiso(Rol.ELIMINAR_REGISTROS):
                ctk.CTkButton(fila, text="Eliminar", width=80, fg_color="#B3261E",
                              command=lambda reg=r: self._eliminar(reg)).pack(side="right", padx=6)
            if self.rol.tiene_permiso(Rol.ACTUALIZAR_REGISTROS):
                ctk.CTkButton(fila, text="Editar", width=80,
                              command=lambda reg=r: self._editar(reg)).pack(side="right", padx=6)
 
    def _construir_mis_horas(self, contenedor) -> None:
        if self.rol.tiene_permiso(Rol.CREAR_REGISTRO_PROPIO):
            ctk.CTkButton(contenedor, text="Cargar horas (rango de fechas)",
                          command=self._abrir_carga_masiva).pack(anchor="w", pady=(10, 5))
        self.lista_mias = ctk.CTkScrollableFrame(contenedor)
        self.lista_mias.pack(fill="both", expand=True, pady=(5, 10))
        self._cargar_mis_registros()
 
    def _cargar_mis_registros(self) -> None:
        try:
            registros = registro_tiempo_repo.listar(empleado_id=self.empleado_actual.id)
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("LISTAR_MIS_REGISTROS", "No se pudieron cargar tus horas.", e)
            return
        self._mostrar(self.lista_mias, registros, con_empleado=False)
 
    def _abrir_carga_masiva(self) -> None:
        CargaMasivaView(self, empleado=self.empleado_actual,
                        on_guardado=self._cargar_mis_registros,
                        usuario_id=self.app.usuario_actual.id)
 
    def _construir_todos(self, contenedor) -> None:
        try:
            empleados = empleado_repo.listar_todos(incluir_inactivos=True)
            proyectos = proyecto_repo.listar_todos(incluir_inactivos=True)
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("LISTAR_REGISTROS", "No se pudieron cargar los filtros.", e)
            return
 
        self._mapa_empleados = {f"{e.nombre} (#{e.id})": e.id for e in empleados}
        self._mapa_proyectos = {p.nombre: p.id for p in proyectos}
 
        filtros = ctk.CTkFrame(contenedor, fg_color="transparent")
        filtros.pack(fill="x", pady=(10, 0))
        self.filtro_empleado = ctk.CTkOptionMenu(filtros, values=[self.TODOS, *self._mapa_empleados], width=170)
        self.filtro_proyecto = ctk.CTkOptionMenu(filtros, values=[self.TODOS, *self._mapa_proyectos], width=150)
        self.filtro_desde = ctk.CTkEntry(filtros, placeholder_text="Desde AAAA-MM-DD", width=120)
        self.filtro_hasta = ctk.CTkEntry(filtros, placeholder_text="Hasta AAAA-MM-DD", width=120)
        for control in (
            self.filtro_empleado, self.filtro_proyecto, self.filtro_desde, self.filtro_hasta,
            ctk.CTkButton(filtros, text="Filtrar", width=70, command=self._cargar_todos),
            ctk.CTkButton(filtros, text="Limpiar", width=70, fg_color="gray", command=self._limpiar_filtros),
        ):
            control.pack(side="left", padx=(0, 8))
 
        self.lista_todos = ctk.CTkScrollableFrame(contenedor)
        self.lista_todos.pack(fill="both", expand=True, pady=10)
        self._cargar_todos()
 
    def _leer_fecha(self, entrada, nombre: str):
        texto = entrada.get().strip()
        if not texto:
            return None
        try:
            return datetime.strptime(texto, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"La fecha '{nombre}' debe tener el formato AAAA-MM-DD.") from None
 
    def _cargar_todos(self) -> None:
        try:
            desde = self._leer_fecha(self.filtro_desde, "Desde")
            hasta = self._leer_fecha(self.filtro_hasta, "Hasta")
            if desde and hasta and desde > hasta:
                raise ValueError("'Desde' no puede ser posterior a 'Hasta'.")
        except ValueError as e:
            messagebox.showerror("Filtro inválido", str(e))
            return
        try:
            registros = registro_tiempo_repo.listar(
                empleado_id=self._mapa_empleados.get(self.filtro_empleado.get()),
                proyecto_id=self._mapa_proyectos.get(self.filtro_proyecto.get()),
                desde=desde,
                hasta=hasta,
            )
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("LISTAR_REGISTROS", "No se pudieron cargar los registros.", e)
            return
        self._mostrar(self.lista_todos, registros, con_empleado=True)
 
    def _limpiar_filtros(self) -> None:
        for menu in (self.filtro_empleado, self.filtro_proyecto):
            menu.set(self.TODOS)
        for entrada in (self.filtro_desde, self.filtro_hasta):
            entrada.delete(0, "end")
        self._cargar_todos()
 
    def _editar(self, registro) -> None:
        RegistroFormView(self, on_guardado=self._cargar_todos,
                         registro=registro, usuario_id=self.app.usuario_actual.id)
 
    def _eliminar(self, registro) -> None:
        if not messagebox.askyesno("Confirmar", f"¿Eliminar el registro del {registro.fecha}?"):
            return
        try:
            registro_tiempo_repo.eliminar(registro.id)
            accion(self.app.usuario_actual.id, "ELIMINAR_REGISTRO",
                   f"registro_id={registro.id}, empleado_id={registro.empleado.id}")
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("ELIMINAR_REGISTRO", "No se pudo eliminar el registro.", e)
            return
        self._cargar_todos()
 
 
def _dashboard():
    from gui.dashboard_view import DashboardView
    return DashboardView