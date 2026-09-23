import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from models.proyecto import Proyecto
from models.rol import Rol
from repositorios import proyecto_repo, empleado_repo


class ProyectoFormView(ctk.CTkToplevel):
    """Formulario modal para crear o editar un Proyecto."""

    def __init__(self, parent, *, on_guardado, proyecto_existente: Proyecto | None = None):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self.proyecto_existente = proyecto_existente
        self.title("Editar proyecto" if proyecto_existente else "Nuevo proyecto")
        self.geometry("380x420")
        self.grab_set()

        ctk.CTkLabel(self, text="Nombre").pack(pady=(20, 0))
        self.entrada_nombre = ctk.CTkEntry(self, width=300)
        if proyecto_existente is not None:
            self.entrada_nombre.insert(0, proyecto_existente.nombre)
        self.entrada_nombre.pack()

        ctk.CTkLabel(self, text="Descripción").pack(pady=(15, 0))
        self.entrada_descripcion = ctk.CTkEntry(self, width=300)
        if proyecto_existente is not None:
            self.entrada_descripcion.insert(0, proyecto_existente.descripcion)
        self.entrada_descripcion.pack()

        ctk.CTkLabel(self, text="Fecha inicio (AAAA-MM-DD)").pack(pady=(15, 0))
        self.entrada_fecha = ctk.CTkEntry(self, width=300)
        if proyecto_existente is not None:
            self.entrada_fecha.insert(0, proyecto_existente.fecha_inicio.isoformat())
        self.entrada_fecha.pack()

        ctk.CTkButton(self, text="Guardar", command=self._guardar).pack(pady=30)

    def _guardar(self) -> None:
        try:
            fecha = datetime.strptime(self.entrada_fecha.get(), "%Y-%m-%d").date()

            if self.proyecto_existente is None:
                nuevo = Proyecto(
                    id=None, nombre=self.entrada_nombre.get(),
                    descripcion=self.entrada_descripcion.get(), fecha_inicio=fecha,
                )
                proyecto_repo.crear(nuevo)
            else:
                p = self.proyecto_existente
                p.nombre = self.entrada_nombre.get()
                p.descripcion = self.entrada_descripcion.get()
                p.fecha_inicio = fecha
                proyecto_repo.actualizar(p)

        except (ValueError, TypeError) as e:
            messagebox.showerror("Datos inválidos", str(e))
            return

        self.on_guardado()
        self.destroy()


class NominaProyectoView(ctk.CTkToplevel):
    """Ventana para agregar/quitar empleados de un proyecto (relación N:M)."""

    def __init__(self, parent, *, proyecto_id: int, on_cambio):
        super().__init__(parent)
        self.proyecto_id = proyecto_id
        self.on_cambio = on_cambio
        self.title("Participantes del proyecto")
        self.geometry("420x480")
        self.grab_set()

        self.lista = ctk.CTkScrollableFrame(self, label_text="Empleados asignados")
        self.lista.pack(fill="both", expand=True, padx=15, pady=15)

        agregar = ctk.CTkFrame(self, fg_color="transparent")
        agregar.pack(fill="x", padx=15, pady=(0, 15))
        self.selector_nuevo = ctk.CTkOptionMenu(agregar, values=["(sin candidatos)"])
        self.selector_nuevo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(agregar, text="Agregar", width=90, command=self._agregar).pack(side="left")

        self._recargar()

    def _recargar(self) -> None:
        for widget in self.lista.winfo_children():
            widget.destroy()

        proyecto = proyecto_repo.buscar_por_id(self.proyecto_id)
        asignados_ids = {e.id for e in proyecto.empleados}

        for empleado in proyecto.empleados:
            fila = ctk.CTkFrame(self.lista)
            fila.pack(fill="x", pady=3)
            ctk.CTkLabel(fila, text=empleado.nombre).pack(side="left", padx=10, pady=6)
            ctk.CTkButton(
                fila, text="Quitar", width=80, fg_color="#B3261E",
                command=lambda e=empleado: self._quitar(e),
            ).pack(side="right", padx=6)

        candidatos = [e for e in empleado_repo.listar_todos() if e.id not in asignados_ids]
        self._mapa_candidatos = {e.nombre: e for e in candidatos}
        valores = list(self._mapa_candidatos.keys()) or ["(sin candidatos)"]
        self.selector_nuevo.configure(values=valores)
        self.selector_nuevo.set(valores[0])

    def _agregar(self) -> None:
        seleccion = self.selector_nuevo.get()
        if seleccion not in self._mapa_candidatos:
            return
        empleado = self._mapa_candidatos[seleccion]
        try:
            proyecto_repo.asignar_empleado(self.proyecto_id, empleado.id)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        self._recargar()
        self.on_cambio()

    def _quitar(self, empleado) -> None:
        proyecto_repo.quitar_empleado(self.proyecto_id, empleado.id)
        self._recargar()
        self.on_cambio()


class ProyectosView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._mostrar_inactivos = False
        rol = app.usuario_actual.rol

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(encabezado, text="← Volver", width=90,
                      command=lambda: app.navegar_a(_dashboard())).pack(side="left")
        ctk.CTkLabel(encabezado, text="Proyectos", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)
        if rol.tiene_permiso(Rol.ASIGNAR_EMPLEADOS_PROYECTO):
            ctk.CTkButton(encabezado, text="+ Nuevo proyecto",
                          command=self._abrir_formulario_crear).pack(side="right")

        self.switch_inactivos = ctk.CTkSwitch(
            self, text="Mostrar inactivos", command=self._toggle_inactivos
        )
        self.switch_inactivos.pack(anchor="w", padx=20)

        self.lista = ctk.CTkScrollableFrame(self)
        self.lista.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self._cargar_lista()

    def _toggle_inactivos(self) -> None:
        self._mostrar_inactivos = self.switch_inactivos.get() == 1
        self._cargar_lista()

    def _cargar_lista(self) -> None:
        for widget in self.lista.winfo_children():
            widget.destroy()

        rol = self.app.usuario_actual.rol
        proyectos = proyecto_repo.listar_todos(incluir_inactivos=self._mostrar_inactivos)

        for proyecto in proyectos:
            fila = ctk.CTkFrame(self.lista)
            fila.pack(fill="x", pady=4)

            estado = "" if proyecto.activo else "  [INACTIVO]"
            texto = f"{proyecto.nombre}{estado}  ·  {len(proyecto.empleados)} participante(s)"
            ctk.CTkLabel(fila, text=texto).pack(side="left", padx=10, pady=8)

            if not rol.tiene_permiso(Rol.ASIGNAR_EMPLEADOS_PROYECTO):
                continue

            if proyecto.activo:
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
        ProyectoFormView(self, on_guardado=self._cargar_lista)

    def _abrir_formulario_editar(self, proyecto: Proyecto) -> None:
        ProyectoFormView(self, on_guardado=self._cargar_lista, proyecto_existente=proyecto)

    def _abrir_nomina(self, proyecto: Proyecto) -> None:
        NominaProyectoView(self, proyecto_id=proyecto.id, on_cambio=self._cargar_lista)

    def _desactivar(self, proyecto: Proyecto) -> None:
        if messagebox.askyesno("Confirmar", f"¿Desactivar '{proyecto.nombre}'?"):
            proyecto_repo.eliminar(proyecto.id)
            self._cargar_lista()

    def _reactivar(self, proyecto: Proyecto) -> None:
        proyecto_repo.activar(proyecto.id)
        self._cargar_lista()


def _dashboard():
    from gui.dashboard_view import DashboardView
    return DashboardView