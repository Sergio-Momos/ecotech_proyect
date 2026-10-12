import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from models.proyecto import Proyecto
from models.rol import Rol
from repositorios import proyecto_repo, empleado_repo
from utils.auditoria import accion, error as log_error


class ProyectoFormView(ctk.CTkToplevel):
    """Formulario modal para crear o editar un Proyecto."""

    def __init__(self, parent, *, on_guardado, usuario_id,proyecto_existente: Proyecto | None = None):
        super().__init__(parent)
        self._on_guardado = on_guardado
        self._proyecto_existente = proyecto_existente
        self.title("Editar proyecto" if proyecto_existente else "Nuevo proyecto")
        self.geometry("380x420")
        self.grab_set()
        self._usuario_id = usuario_id

        ctk.CTkLabel(self, text="Nombre").pack(pady=(20, 0))
        self._entrada_nombre = ctk.CTkEntry(self, width=300)
        if proyecto_existente is not None:
            self._entrada_nombre.insert(0, proyecto_existente._nombre)
        self._entrada_nombre.pack()

        ctk.CTkLabel(self, text="Descripción").pack(pady=(15, 0))
        self._entrada_descripcion = ctk.CTkEntry(self, width=300)
        if proyecto_existente is not None:
            self._entrada_descripcion.insert(0, proyecto_existente._descripcion)
        self._entrada_descripcion.pack()

        ctk.CTkLabel(self, text="Fecha inicio (AAAA-MM-DD)").pack(pady=(15, 0))
        self._entrada_fecha = ctk.CTkEntry(self, width=300)
        if proyecto_existente is not None:
            self._entrada_fecha.insert(0, proyecto_existente._fecha_inicio.isoformat())
        self._entrada_fecha.pack()

        ctk.CTkButton(self, text="Guardar", command=self._guardar).pack(pady=30)

    def _guardar(self) -> None:
        try:
            fecha = datetime.strptime(self._entrada_fecha.get(), "%Y-%m-%d").date()

            if self._proyecto_existente is None:
                nuevo = Proyecto(
                    id=None, nombre=self._entrada_nombre.get(),
                    descripcion=self._entrada_descripcion.get(), fecha_inicio=fecha,
                )
                proyecto_repo.crear(nuevo)
                accion(self._usuario_id, "CREAR_PROYECTO", f"Proyecto_id={nuevo._id}")
            else:
                p = self._proyecto_existente
                p._nombre = self._entrada_nombre.get()
                p._descripcion = self._entrada_descripcion.get()
                p._fecha_inicio = fecha
                proyecto_repo.actualizar(p)
                accion(self._usuario_id, "ACTUALIZAR_PROYECTO", f"Proyecto_id={p._id}")

        except (ValueError, TypeError) as e:
            log_error(self._usuario_id, "CREAR_PROYECTO" if self._proyecto_existente is None
                    else "ACTUALIZAR_PROYECTO", str(e))
            messagebox.showerror("Datos inválidos", str(e))
            return

        self._on_guardado()
        self.destroy()


class NominaProyectoView(ctk.CTkToplevel):
    """Ventana para agregar/quitar empleados de un proyecto (relación N:M)."""

    def __init__(self, parent, *, proyecto_id: int, on_cambio, usuario_id: int):
        super().__init__(parent)
        self._proyecto_id = proyecto_id
        self._on_cambio = on_cambio
        self.title("Participantes del proyecto")
        self.geometry("420x480")
        self.grab_set()
        self._usuario_id = usuario_id

        self._lista = ctk.CTkScrollableFrame(self, label_text="Empleados asignados")
        self._lista.pack(fill="both", expand=True, padx=15, pady=15)

        agregar = ctk.CTkFrame(self, fg_color="transparent")
        agregar.pack(fill="x", padx=15, pady=(0, 15))
        self._selector_nuevo = ctk.CTkOptionMenu(agregar, values=["(sin candidatos)"])
        self._selector_nuevo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(agregar, text="Agregar", width=90, command=self._agregar).pack(side="left")

        self._recargar()

    def _recargar(self) -> None:
        for widget in self._lista.winfo_children():
            widget.destroy()

        proyecto = proyecto_repo.buscar_por_id(self._proyecto_id)
        asignados_ids = {e._id for e in proyecto._empleados}

        for empleado in proyecto._empleados:
            fila = ctk.CTkFrame(self._lista)
            fila.pack(fill="x", pady=3)
            ctk.CTkLabel(fila, text=empleado._nombre).pack(side="left", padx=10, pady=6)
            ctk.CTkButton(
                fila, text="Quitar", width=80, fg_color="#902923",
                command=lambda e=empleado: self._quitar(e),
            ).pack(side="right", padx=6)

        candidatos = [e for e in empleado_repo.listar_todos() if e._id not in asignados_ids]
        self._mapa_candidatos = {e._nombre: e for e in candidatos}
        valores = list(self._mapa_candidatos.keys()) or ["(sin candidatos)"]
        self._selector_nuevo.configure(values=valores)
        self._selector_nuevo.set(valores[0])

    def _agregar(self) -> None:
        seleccion = self._selector_nuevo.get()
        if seleccion not in self._mapa_candidatos:
            return
        empleado = self._mapa_candidatos[seleccion]
        try:
            proyecto_repo.asignar_empleado(self._proyecto_id, empleado._id)
            accion(self._usuario_id, "ASIGNAR_EMPLEADO_PROYECTO",
                        f"pryt_id={self._proyecto_id}, empleado_id={empleado._id}")
        except ValueError as e:
            log_error(self._usuario_id, "ASIGNAR_EMPLEADO_PROYECTO", str(e))
            messagebox.showerror("Error", str(e))
            return
        self._recargar()
        self._on_cambio()

    def _quitar(self, empleado) -> None:
        proyecto_repo.quitar_empleado(self._proyecto_id, empleado._id)
        accion(self._usuario_id, "QUITAR_EMPLEADO_PROYECTO",
                    f"pryt_id={self._proyecto_id}, empleado_id={empleado._id}")
        self._recargar()
        self._on_cambio()


class ProyectosView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self._mostrar_inactivos = False
        rol = app._usuario_actual._rol

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(encabezado, text="← Volver", width=90,
                      command=lambda: app.navegar_a(_dashboard())).pack(side="left")
        ctk.CTkLabel(encabezado, text="Proyectos", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)
        if rol.tiene_permiso(Rol._ASIGNAR_EMPLEADOS_PROYECTO):
            ctk.CTkButton(encabezado, text="+ Nuevo proyecto",
                          command=self._abrir_formulario_crear).pack(side="right")

        self._switch_inactivos = ctk.CTkSwitch(
            self, text="Mostrar inactivos", command=self._toggle_inactivos
        )
        self._switch_inactivos.pack(anchor="w", padx=20)

        self._lista = ctk.CTkScrollableFrame(self)
        self._lista.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self._cargar_lista()

    def _toggle_inactivos(self) -> None:
        self._mostrar_inactivos = self._switch_inactivos.get() == 1
        self._cargar_lista()

    def _cargar_lista(self) -> None:
        for widget in self._lista.winfo_children():
            widget.destroy()

        rol = self._app._usuario_actual._rol
        proyectos = proyecto_repo.listar_todos(incluir_inactivos=self._mostrar_inactivos)

        for proyecto in proyectos:
            fila = ctk.CTkFrame(self._lista)
            fila.pack(fill="x", pady=4)

            estado = "" if proyecto._activo else "  [INACTIVO]"
            texto = f"{proyecto._nombre}{estado}  ·  {len(proyecto._empleados)} participante(s)"
            ctk.CTkLabel(fila, text=texto).pack(side="left", padx=10, pady=8)

            if not rol.tiene_permiso(Rol._ASIGNAR_EMPLEADOS_PROYECTO):
                continue

            if proyecto._activo:
                ctk.CTkButton(fila, text="Desactivar", width=90, fg_color="#B3261E",
                              command=lambda p=proyecto: self._desactivar(p)).pack(side="right", padx=6)
                ctk.CTkButton(fila, text="Participantes", width=100,
                              command=lambda p=proyecto: self._abrir_nomina(p)).pack(side="right", padx=6)
                ctk.CTkButton(fila, text="Editar", width=90,
                              command=lambda p=proyecto: self._abrir_formulario_editar(p)).pack(side="right", padx=6)
            else:
                ctk.CTkButton(fila, text="Reactivar", width=90,
                              command=lambda p=proyecto: self._reactivar(p)).pack(side="right", padx=6)

    def _abrir_formulario_crear(self) -> None:
        ProyectoFormView(self, on_guardado=self._cargar_lista,
                        usuario_id=self._app._usuario_actual._id)

    def _abrir_formulario_editar(self, proyecto: Proyecto) -> None:
        ProyectoFormView(self, on_guardado=self._cargar_lista, proyecto_existente=proyecto,
                        usuario_id=self._app._usuario_actual._id)

    def _abrir_nomina(self, proyecto: Proyecto) -> None:
        NominaProyectoView(self, proyecto_id=proyecto._id,
                        on_cambio=self._cargar_lista,
                        usuario_id=self._app._usuario_actual._id)

    def _desactivar(self, proyecto: Proyecto) -> None:
        if messagebox.askyesno("Confirmar", f"¿Desactivar '{proyecto._nombre}'?"):
            proyecto_repo.eliminar(proyecto._id)
            accion(self._app._usuario_actual._id, "DESACTIVAR_PROYECTO",
                            f"pryt_id={proyecto._id}")
            self._cargar_lista()

    def _reactivar(self, proyecto: Proyecto) -> None:
        proyecto_repo.activar(proyecto._id)
        accion(self._app._usuario_actual._id, "ACTIVAR_PROYECTO",
                                    f"pryt_id={proyecto._id}")
        self._cargar_lista()


def _dashboard():
    from gui.dashboard_view import DashboardView
    return DashboardView