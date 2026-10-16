import customtkinter as ctk
from tkinter import messagebox

from models.departamento import Departamento
from models.rol import Rol
from repositorios import departamento_repo, empleado_repo
from gui.componentes import crear_encabezado, limpiar_contenedor
from utils.auditoria import accion, error as log_error

class DepartamentoFormView(ctk.CTkToplevel):
    def __init__(self, parent, *,on_guardado, usuario_id,departamento_existente=None):
        super().__init__(parent)
        self._on_guardado = on_guardado
        self._departamento_existente = departamento_existente
        self.title("Editar departamento" if departamento_existente else "Nuevo departamento")
        self.geometry("360x280")
        self.grab_set()
        self._usuario_id = usuario_id

        ctk.CTkLabel(self, text="Nombre").pack(pady=(20, 0))
        self._entrada_nombre = ctk.CTkEntry(self, width=280)
        if departamento_existente is not None:
            self._entrada_nombre.insert(0, departamento_existente._nombre)
        self._entrada_nombre.pack()

        ctk.CTkLabel(self, text="Gerente").pack(pady=(20, 0))
        empleados = empleado_repo.listar_todos()
        self._mapa_empleados = {f"{e._nombre} (RUT {e._rut})": e for e in empleados}
        valores = list(self._mapa_empleados.keys()) or ["No hay empleados disponibles"]
        self._selector_gerente = ctk.CTkOptionMenu(self, values=valores, width=280)
        self._selector_gerente.pack()

        if departamento_existente is not None:
            for texto, emp in self._mapa_empleados.items():
                if emp._id == departamento_existente._gerente._id:
                    self._selector_gerente.set(texto)
                    break

        ctk.CTkButton(self, text="Guardar", command=self._guardar).pack(pady=30)

    def _guardar(self) -> None:
        seleccion = self._selector_gerente.get()
        if seleccion not in self._mapa_empleados:
            log_error(self._usuario_id,"CREAR_DEPARTAMENTO" ,"GERENTE_INVALIDO")
            messagebox.showerror("Datos inválidos", "Debe seleccionar un gerente válido.")
            return
        gerente = self._mapa_empleados[seleccion]

        try:
            if self._departamento_existente is None:
                nuevo = Departamento(id=None, nombre=self._entrada_nombre.get(), gerente=gerente)
                departamento_repo.crear(nuevo)
                accion(self._usuario_id, "CREAR_DEPARTAMENTO", f"Departamento_id={nuevo._id}")
            else:
                depto = self._departamento_existente
                depto._nombre = self._entrada_nombre.get()
                depto._gerente = gerente
                departamento_repo.actualizar(depto)
                accion(self._usuario_id, "ACTUALIZAR_DEPARTAMENTO", f"Departamento_id={depto._id}")
        except (ValueError, TypeError) as e:
            log_error(self._usuario_id, "CREAR_DEPARTAMENTO" if self._departamento_existente is None
                    else "ACTUALIZAR_DEPARTAMENTO", str(e))
            messagebox.showerror("Datos inválidos", str(e))
            return

        self._on_guardado()
        self.destroy()


class NominaDepartamentoView(ctk.CTkToplevel):
    """Ventana para agregar/quitar empleados de un departamento ya existente."""

    def __init__(self, parent, departamento_id: int, on_cambio, *, usuario_id: int):
        super().__init__(parent)
        self._departamento_id = departamento_id
        self._on_cambio = on_cambio
        self.title("Nómina del departamento")
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
        limpiar_contenedor(self._lista)

        depto = departamento_repo.buscar_por_id(self._departamento_id)
        asignados_ids = {e._id for e in depto._empleados}

        for empleado in depto._empleados:
            fila = ctk.CTkFrame(self._lista)
            fila.pack(fill="x", pady=3)
            ctk.CTkLabel(fila, text=empleado._nombre).pack(side="left", padx=10, pady=6)
            ctk.CTkButton(
                fila, text="Quitar", width=80, fg_color="#B3261E",
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
        departamento_repo.asignar_empleado(self._departamento_id, empleado._id)
        accion(self._usuario_id, "ASIGNAR_EMPLEADO_DPTO",
            f"dpto_id={self._departamento_id}, empleado_id={empleado._id}")
        self._recargar()
        self._on_cambio()

    def _quitar(self, empleado) -> None:
        departamento_repo.quitar_empleado(empleado._id)
        accion(self._usuario_id, "QUITAR_EMPLEADO_DPTO",
            f"dpto_id={self._departamento_id}, empleado_id={empleado._id}")
        self._recargar()
        self._on_cambio()


class DepartamentosView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        rol = app._usuario_actual._rol

        encabezado = crear_encabezado(self, app, "Departamentos")
        if rol.tiene_permiso(Rol._ASIGNAR_EMPLEADOS_DEPARTAMENTO):
            ctk.CTkButton(encabezado, text="+ Nuevo departamento",
                          command=self._abrir_formulario_crear).pack(side="right")

        self._lista = ctk.CTkScrollableFrame(self)
        self._lista.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._cargar_lista()

    def _cargar_lista(self) -> None:
        limpiar_contenedor(self._lista)

        rol = self._app._usuario_actual._rol
        for depto in departamento_repo.listar_todos():
            fila = ctk.CTkFrame(self._lista)
            fila.pack(fill="x", pady=4)

            texto = f"{depto._nombre}  ·  Gerente: {depto._gerente.get_nombre_completo()}  ·  {len(depto._empleados)} empleado(s)"
            ctk.CTkLabel(fila, text=texto).pack(side="left", padx=10, pady=8)

            if rol.tiene_permiso(Rol._ASIGNAR_EMPLEADOS_DEPARTAMENTO):
                ctk.CTkButton(fila, text="Eliminar", width=90, fg_color="#B3261E",
                              command=lambda d=depto: self._eliminar(d)).pack(side="right", padx=6)
                ctk.CTkButton(fila, text="Nómina", width=90,
                              command=lambda d=depto: self._abrir_nomina(d)).pack(side="right", padx=6)
                ctk.CTkButton(fila, text="Editar", width=90,
                              command=lambda d=depto: self._abrir_formulario_editar(d)).pack(side="right", padx=6)

    def _abrir_formulario_crear(self) -> None:
        DepartamentoFormView(self, on_guardado=self._cargar_lista,
                            usuario_id=self._app._usuario_actual._id)

    def _abrir_formulario_editar(self, depto: Departamento) -> None:
        DepartamentoFormView(self, on_guardado=self._cargar_lista,
                            usuario_id=self._app._usuario_actual._id,
                            departamento_existente=depto)

    def _abrir_nomina(self, depto: Departamento) -> None:
        NominaDepartamentoView(self, departamento_id=depto._id,
                                usuario_id=self._app._usuario_actual._id,
                                on_cambio=self._cargar_lista)

    def _eliminar(self, depto: Departamento) -> None:
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{depto._nombre}'?..."):
            departamento_repo.eliminar(depto._id)
            accion(self._app._usuario_actual._id, "ELIMINAR_DEPARTAMENTO",
                f"dpto_id={depto._id}")
            self._cargar_lista()
