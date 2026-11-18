import customtkinter as ctk
from tkinter import messagebox

from models.departamento import Departamento
from models.rol import Rol
from repositorios import departamento_repo, empleado_repo
from utils.auditoria import accion, error as log_error
from mysql.connector import Error as ErrorBD


class DepartamentoFormView(ctk.CTkToplevel):
    def __init__(self, parent, *, on_guardado, usuario_id, departamento_existente=None):
        super().__init__(parent)
        self.on_guardado = on_guardado
        self.departamento_existente = departamento_existente
        self.title("Editar departamento" if departamento_existente else "Nuevo departamento")
        self.geometry("360x280")
        self.grab_set()
        self.usuario_id = usuario_id

        ctk.CTkLabel(self, text="Nombre").pack(pady=(20, 0))
        self.entrada_nombre = ctk.CTkEntry(self, width=280)
        if departamento_existente is not None:
            self.entrada_nombre.insert(0, departamento_existente.nombre)
        self.entrada_nombre.pack()

        ctk.CTkLabel(self, text="Gerente").pack(pady=(20, 0))
        propios = list(departamento_existente.empleados) if departamento_existente else []
        ids_propios = {e.id for e in propios}
        libres = [e for e in empleado_repo.listar_sin_departamento() if e.id not in ids_propios]
        self._mapa_empleados = {f"{e.get_nombre_completo()} (#{e.id})": e for e in propios + libres}
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
        accion_log = "CREAR_DEPARTAMENTO" if self.departamento_existente is None else "ACTUALIZAR_DEPARTAMENTO"
        seleccion = self.selector_gerente.get()
        if seleccion not in self._mapa_empleados:
            log_error(self.usuario_id, accion_log, "GERENTE_INVALIDO")
            messagebox.showerror("Datos inválidos", "Debe seleccionar un gerente válido.")
            return
        gerente = self._mapa_empleados[seleccion]

        try:
            if self.departamento_existente is None:
                nuevo = Departamento(id=None, nombre=self.entrada_nombre.get(), gerente=gerente)
                departamento_repo.crear(nuevo)
                accion(self.usuario_id, accion_log, f"Departamento_id={nuevo.id}")
            else:
                depto = self.departamento_existente
                depto.nombre = self.entrada_nombre.get()
                depto.gerente = gerente
                departamento_repo.actualizar(depto)
                accion(self.usuario_id, accion_log, f"Departamento_id={depto.id}")
        except (ValueError, TypeError) as e:
            log_error(self.usuario_id, accion_log, str(e))
            messagebox.showerror("Datos inválidos", str(e))
            return
        except (ConnectionError, ErrorBD) as e:
            log_error(self.usuario_id, accion_log, str(e))
            messagebox.showerror("Error de base de datos", "No se pudo guardar el departamento.")
            return

        self.on_guardado()
        self.destroy()


class NominaDepartamentoView(ctk.CTkToplevel):
    def __init__(self, parent, departamento_id: int, on_cambio, *, usuario_id: int):
        super().__init__(parent)
        self.departamento_id = departamento_id
        self.on_cambio = on_cambio
        self.title("Nómina del departamento")
        self.geometry("420x480")
        self.grab_set()
        self.usuario_id = usuario_id

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

        try:
            depto = departamento_repo.buscar_por_id(self.departamento_id)
            candidatos = empleado_repo.listar_sin_departamento()
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("CARGAR_NOMINA", "No se pudo cargar la nómina.", e)
            return

        for empleado in depto.empleados:
            fila = ctk.CTkFrame(self.lista)
            fila.pack(fill="x", pady=3)
            es_gerente = empleado.id == depto.gerente.id
            texto = f"{empleado.get_nombre_completo()} (gerente)" if es_gerente else empleado.get_nombre_completo()
            ctk.CTkLabel(fila, text=texto).pack(side="left", padx=10, pady=6)
            if not es_gerente:
                ctk.CTkButton(
                    fila, text="Quitar", width=80, fg_color="#B3261E",
                    command=lambda e=empleado: self._quitar(e),
                ).pack(side="right", padx=6)

        self._mapa_candidatos = {f"{e.get_nombre_completo()} (#{e.id})": e for e in candidatos}
        valores = list(self._mapa_candidatos.keys()) or ["(sin candidatos)"]
        self.selector_nuevo.configure(values=valores)
        self.selector_nuevo.set(valores[0])

    def _agregar(self) -> None:
        seleccion = self.selector_nuevo.get()
        if seleccion not in self._mapa_candidatos:
            return
        empleado = self._mapa_candidatos[seleccion]
        try:
            departamento_repo.asignar_empleado(self.departamento_id, empleado.id)
            accion(self.usuario_id, "ASIGNAR_EMPLEADO_DPTO",
                   f"dpto_id={self.departamento_id}, empleado_id={empleado.id}")
        except ValueError as e:
            log_error(self.usuario_id, "ASIGNAR_EMPLEADO_DPTO", str(e))
            messagebox.showerror("No se pudo asignar", str(e))
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("ASIGNAR_EMPLEADO_DPTO", "No se pudo asignar el empleado.", e)
        self._recargar()
        self.on_cambio()

    def _quitar(self, empleado) -> None:
        try:
            departamento_repo.quitar_empleado(empleado.id)
            accion(self.usuario_id, "QUITAR_EMPLEADO_DPTO",
                   f"dpto_id={self.departamento_id}, empleado_id={empleado.id}")
        except (ConnectionError, ErrorBD) as e:
            self._error_bd("QUITAR_EMPLEADO_DPTO", "No se pudo quitar el empleado.", e)
        self._recargar()
        self.on_cambio()

    def _error_bd(self, accion_log: str, mensaje: str, e: Exception) -> None:
        log_error(self.usuario_id, accion_log, str(e))
        messagebox.showerror("Error de base de datos", mensaje)


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

        try:
            departamentos = departamento_repo.listar_todos()
        except (ConnectionError, ErrorBD) as e:
            log_error(self.app.usuario_actual.id, "LISTAR_DEPARTAMENTOS", str(e))
            messagebox.showerror("Error de base de datos", "No se pudo cargar la lista de departamentos.")
            return

        rol = self.app.usuario_actual.rol
        for depto in departamentos:
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
        DepartamentoFormView(self, on_guardado=self._cargar_lista,
                             usuario_id=self.app.usuario_actual.id)

    def _abrir_formulario_editar(self, depto: Departamento) -> None:
        DepartamentoFormView(self, on_guardado=self._cargar_lista,
                             usuario_id=self.app.usuario_actual.id,
                             departamento_existente=depto)

    def _abrir_nomina(self, depto: Departamento) -> None:
        NominaDepartamentoView(self, departamento_id=depto.id,
                               usuario_id=self.app.usuario_actual.id,
                               on_cambio=self._cargar_lista)

    def _eliminar(self, depto: Departamento) -> None:
        if not messagebox.askyesno("Confirmar", f"¿Eliminar '{depto.nombre}'?"):
            return
        try:
            departamento_repo.eliminar(depto.id)
            accion(self.app.usuario_actual.id, "ELIMINAR_DEPARTAMENTO", f"dpto_id={depto.id}")
        except (ConnectionError, ErrorBD) as e:
            log_error(self.app.usuario_actual.id, "ELIMINAR_DEPARTAMENTO", str(e))
            messagebox.showerror("Error de base de datos", f"No se pudo eliminar '{depto.nombre}'.")
            return
        self._cargar_lista()


def _dashboard():
    from gui.dashboard_view import DashboardView
    return DashboardView