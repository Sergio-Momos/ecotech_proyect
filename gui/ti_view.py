import customtkinter as ctk
from tkinter import messagebox

from models.rol import Rol
from repositorios import empleado_repo, usuario_repo, rol_repo
from gui.componentes import crear_encabezado, limpiar_contenedor
from utils.auditoria import accion, error as log_error


class CrearUsuarioView(ctk.CTkToplevel):
    def __init__(self, parent, *, empleado, on_guardado, usuario_id: int):
        super().__init__(parent)
        self._empleado = empleado
        self._on_guardado = on_guardado
        self._usuario_id = usuario_id
        self.title(f"Crear cuenta — {empleado._nombre}")
        self.geometry("360x360")
        self.grab_set()

        ctk.CTkLabel(self, text=f"Empleado: {empleado._nombre}",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self, text=f"ID: {empleado._id}", text_color="gray").pack(pady=(0, 20))

        ctk.CTkLabel(self, text="Contraseña inicial").pack(pady=(5, 0))
        self._entrada_password = ctk.CTkEntry(self, width=280, show="*")
        self._entrada_password.pack()

        ctk.CTkLabel(self, text="Confirmar contraseña").pack(pady=(15, 0))
        self._entrada_confirmar = ctk.CTkEntry(self, width=280, show="*")
        self._entrada_confirmar.pack()

        ctk.CTkLabel(self, text="Rol").pack(pady=(15, 0))
        roles = rol_repo.listar_todos()
        self._mapa_roles = {
            r._nombre: r for r in roles
            if r._perfil_bd != "ti" and r._perfil_bd != "auth"
        }
        valores = list(self._mapa_roles.keys()) or ["(sin roles disponibles)"]
        self._selector_rol = ctk.CTkOptionMenu(self, values=valores, width=280)
        self._selector_rol.pack()

        ctk.CTkButton(self, text="Crear cuenta", command=self._crear).pack(pady=30)

    def _crear(self) -> None:
        password = self._entrada_password.get()
        confirmar = self._entrada_confirmar.get()

        if password != confirmar:
            log_error(self._usuario_id, "CREAR_USUARIO",
                      f"empleado_id={self._empleado._id} | contraseñas no coinciden")
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        if self._selector_rol.get() not in self._mapa_roles:
            log_error(self._usuario_id, "CREAR_USUARIO",
                      f"empleado_id={self._empleado._id} | rol inválido")
            messagebox.showerror("Error", "Selecciona un rol válido.")
            return

        rol = self._mapa_roles[self._selector_rol.get()]
        try:
            usuario = usuario_repo.crear_para_empleado(
                self._empleado, password=password, rol=rol
            )
            accion(self._usuario_id, "CREAR_USUARIO",
                   f"usuario_id={usuario._id}, empleado_id={self._empleado._id}, rol={rol._nombre}")
        except (ValueError, TypeError) as e:
            log_error(self._usuario_id, "CREAR_USUARIO",
                      f"empleado_id={self._empleado._id} | {e}")
            messagebox.showerror("Datos inválidos", str(e))
            return

        messagebox.showinfo("Cuenta creada",
                            f"Usuario: {usuario._username}\n"
                            f"Contraseña entregada de forma segura al empleado.")
        self._on_guardado()
        self.destroy()


class GestionarCuentaView(ctk.CTkToplevel):
    def __init__(self, parent, *, usuario, on_guardado, usuario_id: int):
        super().__init__(parent)
        self._usuario = usuario
        self._on_guardado = on_guardado
        self._usuario_id = usuario_id
        self.title(f"Gestionar cuenta — {usuario._username}")
        self.geometry("360x400")
        self.grab_set()

        ctk.CTkLabel(self, text=f"Usuario: {usuario._username}",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self, text=f"Rol: {usuario._rol._nombre}",
                     text_color="gray").pack(pady=(0, 5))

        estado = "Activo" if usuario._activo else "Inactivo"
        color_estado = "green" if usuario._activo else "red"
        ctk.CTkLabel(self, text=f"Estado: {estado}",
                     text_color=color_estado).pack(pady=(0, 20))

        ctk.CTkLabel(self, text="Nueva contraseña (reseteo)").pack(pady=(5, 0))
        self._entrada_password = ctk.CTkEntry(self, width=280, show="*")
        self._entrada_password.pack()

        ctk.CTkLabel(self, text="Confirmar nueva contraseña").pack(pady=(15, 0))
        self._entrada_confirmar = ctk.CTkEntry(self, width=280, show="*")
        self._entrada_confirmar.pack()

        ctk.CTkButton(self, text="Resetear contraseña",
                      command=self._resetear).pack(pady=(20, 5))

        texto_toggle = "Desactivar cuenta" if usuario._activo else "Reactivar cuenta"
        color_toggle = "#B3261E" if usuario._activo else "#2E7D32"
        ctk.CTkButton(self, text=texto_toggle, fg_color=color_toggle,
                      command=self._toggle_activo).pack(pady=5)

    def _resetear(self) -> None:
        password = self._entrada_password.get()
        confirmar = self._entrada_confirmar.get()

        if password != confirmar:
            log_error(self._usuario_id, "RESETEAR_PASSWORD",
                      f"usuario_id={self._usuario._id} | contraseñas no coinciden")
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        try:
            usuario_repo.cambiar_password(self._usuario._id, password)
            accion(self._usuario_id, "RESETEAR_PASSWORD",
                   f"usuario_id={self._usuario._id}")
        except (ValueError, TypeError) as e:
            log_error(self._usuario_id, "RESETEAR_PASSWORD",
                      f"usuario_id={self._usuario._id} | {e}")
            messagebox.showerror("Datos inválidos", str(e))
            return

        messagebox.showinfo("Listo", "Contraseña actualizada correctamente.")
        self._on_guardado()
        self.destroy()

    def _toggle_activo(self) -> None:
        accion_nombre = "DESACTIVAR_USUARIO" if self._usuario._activo else "REACTIVAR_USUARIO"
        texto = "desactivar" if self._usuario._activo else "reactivar"

        if not messagebox.askyesno("Confirmar", f"¿{texto.capitalize()} esta cuenta?"):
            return

        try:
            if self._usuario._activo:
                usuario_repo.desactivar(self._usuario._id)
            else:
                usuario_repo.activar(self._usuario._id)
            accion(self._usuario_id, accion_nombre,
                   f"usuario_id={self._usuario._id}")
        except Exception as e:
            log_error(self._usuario_id, accion_nombre,
                      f"usuario_id={self._usuario._id} | {e}")
            messagebox.showerror("Error", str(e))
            return

        self._on_guardado()
        self.destroy()


class TiView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app

        crear_encabezado(self, app, "Gestión de usuarios")

        self._tabs = ctk.CTkTabview(self)
        self._tabs.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._tabs.add("Sin cuenta")
        self._construir_sin_cuenta(self._tabs.tab("Sin cuenta"))

        self._tabs.add("Cuentas activas")
        self._construir_con_cuenta(self._tabs.tab("Cuentas activas"), solo_activos=True)

        self._tabs.add("Cuentas inactivas")
        self._construir_con_cuenta(self._tabs.tab("Cuentas inactivas"), solo_activos=False)

    def _construir_sin_cuenta(self, contenedor) -> None:
        self._lista_sin_cuenta = ctk.CTkScrollableFrame(
            contenedor, label_text="Empleados sin cuenta de acceso"
        )
        self._lista_sin_cuenta.pack(fill="both", expand=True, pady=10)
        self._cargar_sin_cuenta()

    def _cargar_sin_cuenta(self) -> None:
        limpiar_contenedor(self._lista_sin_cuenta)

        todos = empleado_repo.listar_todos()
        sin_cuenta = [e for e in todos if usuario_repo.buscar_por_id(e._id) is None]

        if not sin_cuenta:
            ctk.CTkLabel(self._lista_sin_cuenta,
                         text="Todos los empleados tienen cuenta.",
                         text_color="gray").pack(pady=20)
            return

        for empleado in sin_cuenta:
            fila = ctk.CTkFrame(self._lista_sin_cuenta)
            fila.pack(fill="x", pady=3)
            ctk.CTkLabel(fila,
                         text=f"{empleado._nombre}  ·  id={empleado._id}").pack(
                side="left", padx=10, pady=8)
            ctk.CTkButton(
                fila, text="Crear cuenta", width=100,
                command=lambda e=empleado: self._abrir_crear_usuario(e)
            ).pack(side="right", padx=6)

    def _construir_con_cuenta(self, contenedor, solo_activos: bool) -> None:
        lista = ctk.CTkScrollableFrame(contenedor)
        lista.pack(fill="both", expand=True, pady=10)
        self._cargar_cuentas(lista, solo_activos)
        if solo_activos:
            self._lista_activas = lista
        else:
            self._lista_inactivas = lista

    def _cargar_cuentas(self, lista, solo_activos: bool) -> None:
        limpiar_contenedor(lista)

        usuarios = usuario_repo.listar_todos()
        filtrados = [u for u in usuarios
                     if u._activo == solo_activos and u._rol._perfil_bd != "ti"]

        if not filtrados:
            msg = "No hay cuentas activas." if solo_activos else "No hay cuentas inactivas."
            ctk.CTkLabel(lista, text=msg, text_color="gray").pack(pady=20)
            return

        for usuario in filtrados:
            fila = ctk.CTkFrame(lista)
            fila.pack(fill="x", pady=3)
            ctk.CTkLabel(
                fila, text=f"{usuario._username}  ·  {usuario._rol._nombre}  ·  id={usuario._id}"
            ).pack(side="left", padx=10, pady=8)
            ctk.CTkButton(
                fila, text="Gestionar", width=100,
                command=lambda u=usuario: self._abrir_gestionar_cuenta(u)
            ).pack(side="right", padx=6)

    def _abrir_crear_usuario(self, empleado) -> None:
        CrearUsuarioView(self, empleado=empleado, on_guardado=self._recargar_todo,
                         usuario_id=self._app._usuario_actual._id)

    def _abrir_gestionar_cuenta(self, usuario) -> None:
        GestionarCuentaView(self, usuario=usuario, on_guardado=self._recargar_todo,
                            usuario_id=self._app._usuario_actual._id)

    def _recargar_todo(self) -> None:
        self._cargar_sin_cuenta()
        self._cargar_cuentas(self._lista_activas, solo_activos=True)
        self._cargar_cuentas(self._lista_inactivas, solo_activos=False)
