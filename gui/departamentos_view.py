import customtkinter as ctk
from tkinter import messagebox

from models.departamento import Departamento
from models.rol import Rol
from repositorios import departamento_repo, empleado_repo


class DepartamentoFormView(ctk.CTkToplevel):
    def __init__(self, parent, *, on_guardado, departamento_existente=None):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self.departamento_existente = departamento_existente
        self.title("Editar departamento" if departamento_existente else "Nuevo departamento")
        self.geometry("360x280")
        self.grab_set()

        ctk.CTkLabel(self, text="Nombre").pack(pady=(20, 0))
        self.entrada_nombre = ctk.CTkEntry(self, width=280)
        if departamento_existente is not None:
            self.entrada_nombre.insert(0, departamento_existente.nombre)
        self.entrada_nombre.pack()

        ctk.CTkLabel(self, text="Gerente").pack(pady=(20, 0))
        empleados = empleado_repo.listar_todos()
        self._mapa_empleados = {f"{e.nombre} (RUT {e.rut})": e for e in empleados}
        valores = list(self._mapa_empleados.keys()) or ["No hay empleados disponibles"]
        self.selector_gerente = ctk.CTkOptionMenu(self, values=valores, width=280)
        self.selector_gerente.pack()

        if departamento_existente is not None:
            for texto, emp in self._mapa_empleados.items():
                if emp.id == departamento_existente.gerente.id:
                    self.selector_gerente.set(texto)
                    break

        ctk.CTkButton(self, text="Guardar", command=self._guardar).pack(pady=30)

    def _guardar(self) -> None:
        seleccion = self.selector_gerente.get()
        if seleccion not in self._mapa_empleados:
            messagebox.showerror("Datos inválidos", "Debe seleccionar un gerente válido.")
            return
        gerente = self._mapa_empleados[seleccion]

        try:
            if self.departamento_existente is None:
                nuevo = Departamento(id=None, nombre=self.entrada_nombre.get(), gerente=gerente)
                departamento_repo.crear(nuevo)
            else:
                depto = self.departamento_existente
                depto.nombre = self.entrada_nombre.get()
                depto.gerente = gerente
                departamento_repo.actualizar(depto)
        except (ValueError, TypeError) as e:
            messagebox.showerror("Datos inválidos", str(e))
            return

        self.on_guardado()
        self.destroy()


class NominaDepartamentoView(ctk.CTkToplevel):
    """Ventana para agregar/quitar empleados de un departamento ya existente."""

    def __init__(self, parent, departamento_id: int, on_cambio):
        super().__init__(parent)
        self.departamento_id = departamento_id
        self.on_cambio = on_cambio
        self.title("Nómina del departamento")
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

        depto = departamento_repo.buscar_por_id(self.departamento_id)
        asignados_ids = {e.id for e in depto.empleados}

        for empleado in depto.empleados:
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
        departamento_repo.asignar_empleado(self.departamento_id, empleado.id)
        self._recargar()
        self.on_cambio()

    def _quitar(self, empleado) -> None:
        departamento_repo.quitar_empleado(empleado.id)
        self._recargar()
        self.on_cambio()


class DepartamentosView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        rol = app.usuario_actual.rol

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(encabezado, text="← Volver", width=90,
                      command=lambda: app.navegar_a(_dashboard())).pack(side="left")
        ctk.CTkLabel(encabezado, text="Departamentos", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)
        if rol.tiene_permiso(Rol.ASIGNAR_EMPLEADOS_DEPARTAMENTO):
            ctk.CTkButton(encabezado, text="+ Nuevo departamento",
                          command=self._abrir_formulario_crear).pack(side="right")

        self.lista = ctk.CTkScrollableFrame(self)
        self.lista.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._cargar_lista()

    def _cargar_lista(self) -> None:
        for widget in self.lista.winfo_children():
            widget.destroy()

        rol = self.app.usuario_actual.rol
        for depto in departamento_repo.listar_todos():
            fila = ctk.CTkFrame(self.lista)
            fila.pack(fill="x", pady=4)

            texto = f"{depto.nombre}  ·  Gerente: {depto.gerente.get_nombre_completo()}  ·  {len(depto.empleados)} empleado(s)"
            ctk.CTkLabel(fila, text=texto).pack(side="left", padx=10, pady=8)

            if rol.tiene_permiso(Rol.ASIGNAR_EMPLEADOS_DEPARTAMENTO):
                ctk.CTkButton(fila, text="Eliminar", width=90, fg_color="#B3261E",
                              command=lambda d=depto: self._eliminar(d)).pack(side="right", padx=6)
                ctk.CTkButton(fila, text="Nómina", width=90,
                              command=lambda d=depto: self._abrir_nomina(d)).pack(side="right", padx=6)
                ctk.CTkButton(fila, text="Editar", width=90,
                              command=lambda d=depto: self._abrir_formulario_editar(d)).pack(side="right", padx=6)

    def _abrir_formulario_crear(self) -> None:
        DepartamentoFormView(self, on_guardado=self._cargar_lista)

    def _abrir_formulario_editar(self, depto: Departamento) -> None:
        DepartamentoFormView(self, on_guardado=self._cargar_lista, departamento_existente=depto)

    def _abrir_nomina(self, depto: Departamento) -> None:
        NominaDepartamentoView(self, departamento_id=depto.id, on_cambio=self._cargar_lista)

    def _eliminar(self, depto: Departamento) -> None:
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{depto.nombre}'? Sus empleados quedarán sin departamento."):
            departamento_repo.eliminar(depto.id)
            self._cargar_lista()


def _dashboard():
    from gui.dashboard_view import DashboardView
    return DashboardView

