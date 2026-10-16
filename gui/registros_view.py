import customtkinter as ctk
from tkinter import messagebox
from datetime import timedelta, datetime

from models.rol import Rol
from models.registro_tiempo import RegistroTiempo
from repositorios import empleado_repo, proyecto_repo, registro_tiempo_repo
from utils.fechas import leer_fecha_opcional
from gui.componentes import crear_encabezado, limpiar_contenedor
from utils.auditoria import accion, registro_horas, error as log_error
from mysql.connector import Error as ErrorBD


class RegistroFormView(ctk.CTkToplevel):

    def __init__(self, parent, *, on_guardado, registro, usuario):
        super().__init__(parent)
        self._on_guardado = on_guardado
        self._registro = registro
        self._usuario = usuario
        self._usuario_id = usuario._id
        self.title("Editar registro de horas")
        self.geometry("360x460")
        self.grab_set()

        ctk.CTkLabel(self, text=f"Empleado: {registro._empleado._nombre}", text_color="gray").pack(pady=(20, 10))

        ctk.CTkLabel(self, text="Fecha (AAAA-MM-DD)").pack(pady=(5, 0))
        self._entrada_fecha = ctk.CTkEntry(self, width=280)
        self._entrada_fecha.insert(0, registro._fecha.isoformat())
        self._entrada_fecha.pack()

        ctk.CTkLabel(self, text="Horas trabajadas").pack(pady=(15, 0))
        self._entrada_horas = ctk.CTkEntry(self, width=280)
        self._entrada_horas.insert(0, str(registro._horas_trabajadas))
        self._entrada_horas.pack()

        ctk.CTkLabel(self, text="Descripción").pack(pady=(15, 0))
        self._entrada_descripcion = ctk.CTkEntry(self, width=280)
        self._entrada_descripcion.insert(0, registro._descripcion)
        self._entrada_descripcion.pack()

        ctk.CTkLabel(self, text="Proyecto").pack(pady=(15, 0))
        proyectos = proyecto_repo.listar_todos()
        self._mapa_proyectos = {p._nombre: p for p in proyectos}
        self._selector_proyecto = ctk.CTkOptionMenu(
            self, values=list(self._mapa_proyectos.keys()), width=280
        )
        self._mapa_proyectos.setdefault(registro._proyecto._nombre, registro._proyecto)
        self._selector_proyecto.configure(values=list(self._mapa_proyectos))
        self._selector_proyecto.set(registro._proyecto._nombre)
        self._selector_proyecto.pack()

        ctk.CTkButton(self, text="Guardar", command=self._guardar).pack(pady=30)

    def _guardar(self) -> None:
        try:
            nuevo = RegistroTiempo(
                fecha=datetime.strptime(self._entrada_fecha.get(), "%Y-%m-%d").date(),
                horas_trabajadas=float(self._entrada_horas.get()),
                descripcion=self._entrada_descripcion.get(),
                empleado=self._registro._empleado,
                proyecto=self._mapa_proyectos[self._selector_proyecto.get()],
            )
            nuevo._id = self._registro._id
            registro_tiempo_repo.actualizar(nuevo, usuario=self._usuario)
            accion(self._usuario_id, "ACTUALIZAR_REGISTRO",
                   f"registro_id={self._registro._id}, empleado_id={self._registro._empleado._id}")
        except (ValueError, TypeError, KeyError, PermissionError) as e:
            log_error(self._usuario_id, "ACTUALIZAR_REGISTRO", str(e))
            messagebox.showerror("Datos inválidos", str(e))
            return
        except (ConnectionError, ErrorBD) as e:
            log_error(self._usuario_id, "ACTUALIZAR_REGISTRO", str(e))
            messagebox.showerror("Error de base de datos", f"No se pudo guardar el registro.\n{e}")
            return
        self._on_guardado()
        self.destroy()


class CargaMasivaView(ctk.CTkToplevel):

    def __init__(self, parent, *, empleado, on_guardado, usuario):
        super().__init__(parent)
        self._empleado = empleado
        self._on_guardado = on_guardado
        self._usuario = usuario
        self._usuario_id = usuario._id
        self.title("Carga masiva de horas")
        self.geometry("580x620")
        self.grab_set()

        proyectos = proyecto_repo.listar_todos()
        self._mapa_proyectos = {p._nombre: p for p in proyectos}

        controles = ctk.CTkFrame(self, fg_color="transparent")
        controles.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(controles, text="Proyecto").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 5))
        self._selector_proyecto = ctk.CTkOptionMenu(
            controles, values=list(self._mapa_proyectos.keys()) or ["(sin proyectos)"]
        )
        self._selector_proyecto.grid(row=1, column=0, columnspan=4, sticky="we", pady=(0, 10))

        ctk.CTkLabel(controles, text="Desde").grid(row=2, column=0, padx=(0, 5))
        self._entrada_desde = ctk.CTkEntry(controles, placeholder_text="AAAA-MM-DD", width=110)
        self._entrada_desde.grid(row=2, column=1, padx=(0, 15))

        ctk.CTkLabel(controles, text="Hasta").grid(row=2, column=2, padx=(0, 5))
        self._entrada_hasta = ctk.CTkEntry(controles, placeholder_text="AAAA-MM-DD", width=110)
        self._entrada_hasta.grid(row=2, column=3)

        ctk.CTkButton(self, text="Generar tabla", command=self._generar_filas).pack(pady=(0, 10))

        self._contenedor_filas = ctk.CTkScrollableFrame(
            self, label_text="Horas por día (deja en 0 los días no trabajados)"
        )
        self._contenedor_filas.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        self._filas = []

        ctk.CTkButton(self, text="Guardar todo", command=self._guardar_lote).pack(pady=15)

    def _error_bd(self, mensaje: str, e: Exception) -> None:
        log_error(self._usuario_id, "CARGA_MASIVA", str(e))
        messagebox.showerror("Error de base de datos", f"{mensaje}\n{e}")

    def _generar_filas(self) -> None:
        try:
            desde = datetime.strptime(self._entrada_desde.get(), "%Y-%m-%d").date()
            hasta = datetime.strptime(self._entrada_hasta.get(), "%Y-%m-%d").date()
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
                r._fecha for r in registro_tiempo_repo.listar_por_empleado(self._empleado._id)
            }
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("No se pudieron revisar los días ya registrados.", e)
            return

        limpiar_contenedor(self._contenedor_filas)
        self._filas = []

        dia = desde
        while dia <= hasta:
            fila = ctk.CTkFrame(self._contenedor_filas)
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
        if self._selector_proyecto.get() not in self._mapa_proyectos:
            messagebox.showerror("Datos inválidos", "Selecciona un proyecto válido.")
            return
        proyecto = self._mapa_proyectos[self._selector_proyecto.get()]

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
                    dia, horas, entry_descripcion.get() or "Carga masiva", self._empleado, proyecto
                )
            except (ValueError, TypeError) as e:
                messagebox.showerror("Error en el lote", f"Día {dia.isoformat()}: {e}")
                return
            pendientes.append(registro)

        if not pendientes:
            messagebox.showinfo("Nada que guardar", "No ingresaste horas en ninguna fila.")
            return

        try:
            registro_tiempo_repo.crear_lote(pendientes, usuario=self._usuario)
        except (ValueError, TypeError, PermissionError) as e:
            log_error(self._usuario_id, "CARGA_MASIVA", str(e))
            messagebox.showerror("Error en el lote", str(e))
            return
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("No se guardó ningún registro. Puedes reintentar la carga.", e)
            return

        for registro in pendientes:
            self._empleado._agregar_registro_tiempo(registro)
            registro_horas(self._usuario_id, self._empleado._id, proyecto._id,
                           str(registro._fecha), registro._horas_trabajadas)

        messagebox.showinfo("Listo", f"Se guardaron {len(pendientes)} registros.")
        self._on_guardado()
        self.destroy()


class RegistrosView(ctk.CTkFrame):
    TODOS = "(Todos)"

    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self._rol = app._usuario_actual._rol
        self._empleado_actual = empleado_repo.buscar_por_id(app._usuario_actual._id)

        crear_encabezado(self, app, "Registro de horas")

        self._tabs = ctk.CTkTabview(self)
        self._tabs.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        if self._rol.tiene_permiso(Rol._LEER_REGISTROS_PROPIOS):
            self._construir_mis_horas(self._tabs.add("Mis horas"))
        if self._rol.tiene_permiso(Rol._LEER_REGISTROS_TODOS):
            self._construir_todos(self._tabs.add("Todos los registros"))

    def _error_bd(self, accion_log: str, mensaje: str, e: Exception) -> None:
        log_error(self._app._usuario_actual._id, accion_log, str(e))
        messagebox.showerror("Error de base de datos", f"{mensaje}\n{e}")

    def _mostrar(self, lista, registros, con_empleado: bool) -> None:
        limpiar_contenedor(lista)
        if not registros:
            ctk.CTkLabel(lista, text="No hay registros.", text_color="gray").pack(pady=20)
            return
        for r in registros:
            fila = ctk.CTkFrame(lista)
            fila.pack(fill="x", pady=2)
            empleado = f"{r._empleado._nombre}  ·  " if con_empleado else ""
            ctk.CTkLabel(fila, text=f"{r._fecha}  ·  {empleado}{r._horas_trabajadas}h  ·  "
                                    f"{r._proyecto._nombre}  ·  {r._descripcion}").pack(
                side="left", padx=10, pady=6)
            if not con_empleado:
                continue
            if self._rol.tiene_permiso(Rol._ELIMINAR_REGISTROS):
                ctk.CTkButton(fila, text="Eliminar", width=80, fg_color="#B3261E",
                              command=lambda reg=r: self._eliminar(reg)).pack(side="right", padx=6)
            if self._rol.tiene_permiso(Rol._ACTUALIZAR_REGISTROS):
                ctk.CTkButton(fila, text="Editar", width=80,
                              command=lambda reg=r: self._editar(reg)).pack(side="right", padx=6)

    def _construir_mis_horas(self, contenedor) -> None:
        if self._rol.tiene_permiso(Rol._CREAR_REGISTRO_PROPIO):
            ctk.CTkButton(contenedor, text="Cargar horas (rango de fechas)",
                          command=self._abrir_carga_masiva).pack(anchor="w", pady=(10, 5))
        self._lista_mias = ctk.CTkScrollableFrame(contenedor)
        self._lista_mias.pack(fill="both", expand=True, pady=(5, 10))
        self._cargar_mis_registros()

    def _cargar_mis_registros(self) -> None:
        try:
            registros = registro_tiempo_repo.listar(empleado_id=self._empleado_actual._id)
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("LISTAR_MIS_REGISTROS", "No se pudieron cargar tus horas.", e)
            return
        self._mostrar(self._lista_mias, registros, con_empleado=False)

    def _abrir_carga_masiva(self) -> None:
        CargaMasivaView(self, empleado=self._empleado_actual,
                        on_guardado=self._cargar_mis_registros,
                        usuario=self._app._usuario_actual)

    def _construir_todos(self, contenedor) -> None:
        try:
            empleados = empleado_repo.listar_todos(incluir_inactivos=True)
            proyectos = proyecto_repo.listar_todos(incluir_inactivos=True)
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("LISTAR_REGISTROS", "No se pudieron cargar los filtros.", e)
            return

        self._mapa_empleados = {f"{e._nombre} (#{e._id})": e._id for e in empleados}
        self._mapa_proyectos = {p._nombre: p._id for p in proyectos}

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

        self._lista_todos = ctk.CTkScrollableFrame(contenedor)
        self._lista_todos.pack(fill="both", expand=True, pady=10)
        self._cargar_todos()

    def _cargar_todos(self) -> None:
        try:
            desde = leer_fecha_opcional(self.filtro_desde.get(), "Desde")
            hasta = leer_fecha_opcional(self.filtro_hasta.get(), "Hasta")
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
        self._mostrar(self._lista_todos, registros, con_empleado=True)

    def _limpiar_filtros(self) -> None:
        for menu in (self.filtro_empleado, self.filtro_proyecto):
            menu.set(self.TODOS)
        for entrada in (self.filtro_desde, self.filtro_hasta):
            entrada.delete(0, "end")
        self._cargar_todos()

    def _editar(self, registro) -> None:
        RegistroFormView(self, on_guardado=self._cargar_todos,
                         registro=registro, usuario=self._app._usuario_actual)

    def _eliminar(self, registro) -> None:
        if not messagebox.askyesno("Confirmar", f"¿Eliminar el registro del {registro._fecha}?"):
            return
        try:
            registro_tiempo_repo.eliminar(registro._id, usuario=self._app._usuario_actual)
            accion(self._app._usuario_actual._id, "ELIMINAR_REGISTRO",
                   f"registro_id={registro._id}, empleado_id={registro._empleado._id}")
        except (ConnectionError, ErrorBD, PermissionError) as e:
            self._error_bd("ELIMINAR_REGISTRO", "No se pudo eliminar el registro.", e)
            return
        self._cargar_todos()
