import customtkinter as ctk
from tkinter import messagebox

from models.rol import Rol
from repositorios import empleado_repo, usuario_repo, rol_repo


class CrearUsuarioView(ctk.CTkToplevel):
    """TI crea una cuenta nueva para un empleado que todavía no tiene usuario."""

    def __init__(self, parent, *, empleado, on_guardado):
        super().__init__(parent)
        self.empleado = empleado
        self.on_guardado = on_guardado
        self.title(f"Crear cuenta — {empleado.nombre}")
        self.geometry("360x360")
        self.grab_set()

        ctk.CTkLabel(self, text=f"Empleado: {empleado.nombre}",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self, text=f"RUT: {empleado.rut}", text_color="gray").pack(pady=(0, 20))

        ctk.CTkLabel(self, text="Contraseña inicial").pack(pady=(5, 0))
        self.entrada_password = ctk.CTkEntry(self, width=280, show="*")
        self.entrada_password.pack()

        ctk.CTkLabel(self, text="Confirmar contraseña").pack(pady=(15, 0))
        self.entrada_confirmar = ctk.CTkEntry(self, width=280, show="*")
        self.entrada_confirmar.pack()

        ctk.CTkLabel(self, text="Rol").pack(pady=(15, 0))
        roles = rol_repo.listar_todos()
        # TI no puede asignarse a sí mismo ni crear otros TI
        self._mapa_roles = {
            r.nombre: r for r in roles
            if r.perfil_bd != "ti" and r.perfil_bd != "auth"
        }
        valores = list(self._mapa_roles.keys()) or ["(sin roles disponibles)"]
        self.selector_rol = ctk.CTkOptionMenu(self, values=valores, width=280)
        self.selector_rol.pack()

        ctk.CTkButton(self, text="Crear cuenta", command=self._crear).pack(pady=30)

    def _crear(self) -> None:
        password = self.entrada_password.get()
        confirmar = self.entrada_confirmar.get()

        if password != confirmar:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        if self.selector_rol.get() not in self._mapa_roles:
            messagebox.showerror("Error", "Selecciona un rol válido.")
            return

        rol = self._mapa_roles[self.selector_rol.get()]
        try:
            usuario = usuario_repo.crear_para_empleado(
                self.empleado, password=password, rol=rol
            )
        except (ValueError, TypeError) as e:
            messagebox.showerror("Datos inválidos", str(e))
            return

        messagebox.showinfo(
            "Cuenta creada",
            f"Usuario: {usuario.username}\n"
            f"Contraseña: entregada de forma segura al empleado."
        )
        self.on_guardado()
        self.destroy()


class GestionarCuentaView(ctk.CTkToplevel):
    """TI resetea contraseña o desactiva la cuenta de un usuario existente."""

    def __init__(self, parent, *, usuario, on_guardado):
        super().__init__(parent)
        self.usuario = usuario
        self.on_guardado = on_guardado
        self.title(f"Gestionar cuenta — {usuario.username}")
        self.geometry("360x400")
        self.grab_set()

        ctk.CTkLabel(self, text=f"Usuario: {usuario.username}",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self, text=f"Rol: {usuario.rol.nombre}", text_color="gray").pack(pady=(0, 20))

        estado = "Activo" if usuario.activo else "Inactivo"
        color_estado = "green" if usuario.activo else "red"
        ctk.CTkLabel(self, text=f"Estado: {estado}", text_color=color_estado).pack(pady=(0, 20))

        ctk.CTkLabel(self, text="Nueva contraseña (reseteo)").pack(pady=(5, 0))
        self.entrada_password = ctk.CTkEntry(self, width=280, show="*")
        self.entrada_password.pack()

        ctk.CTkLabel(self, text="Confirmar nueva contraseña").pack(pady=(15, 0))
        self.entrada_confirmar = ctk.CTkEntry(self, width=280, show="*")
        self.entrada_confirmar.pack()

        ctk.CTkButton(
            self, text="Resetear contraseña", command=self._resetear
        ).pack(pady=(20, 5))

        texto_toggle = "Desactivar cuenta" if usuario.activo else "Reactivar cuenta"
        color_toggle = "#B3261E" if usuario.activo else "#2E7D32"
        ctk.CTkButton(
            self, text=texto_toggle, fg_color=color_toggle,
            command=self._toggle_activo
        ).pack(pady=5)

    def _resetear(self) -> None:
        password = self.entrada_password.get()
        confirmar = self.entrada_confirmar.get()

        if password != confirmar:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        try:
            usuario_repo.cambiar_password(self.usuario.id, password)
        except (ValueError, TypeError) as e:
            messagebox.showerror("Datos inválidos", str(e))
            return

        messagebox.showinfo("Listo", "Contraseña actualizada correctamente.")
        self.on_guardado()
        self.destroy()

    def _toggle_activo(self) -> None:
        accion = "desactivar" if self.usuario.activo else "reactivar"
        if not messagebox.askyesno("Confirmar", f"¿{accion.capitalize()} esta cuenta?"):
            return
        if self.usuario.activo:
            usuario_repo.desactivar(self.usuario.id)
        else:
            usuario_repo.activar(self.usuario.id)
        self.on_guardado()
        self.destroy()


class TiView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(encabezado, text="← Volver", width=90,
                      command=lambda: app.navegar_a(_dashboard())).pack(side="left")
        ctk.CTkLabel(encabezado, text="Gestión de usuarios",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.tabs.add("Sin cuenta")
        self._construir_sin_cuenta(self.tabs.tab("Sin cuenta"))

        self.tabs.add("Cuentas activas")
        self._construir_con_cuenta(self.tabs.tab("Cuentas activas"), solo_activos=True)

        self.tabs.add("Cuentas inactivas")
        self._construir_con_cuenta(self.tabs.tab("Cuentas inactivas"), solo_activos=False)

    def _construir_sin_cuenta(self, contenedor) -> None:
        self.lista_sin_cuenta = ctk.CTkScrollableFrame(
            contenedor, label_text="Empleados sin cuenta de acceso"
        )
        self.lista_sin_cuenta.pack(fill="both", expand=True, pady=10)
        self._cargar_sin_cuenta()

    def _cargar_sin_cuenta(self) -> None:
        for widget in self.lista_sin_cuenta.winfo_children():
            widget.destroy()

        todos = empleado_repo.listar_todos()
        sin_cuenta = [e for e in todos if usuario_repo.buscar_por_id(e.id) is None]

        if not sin_cuenta:
            ctk.CTkLabel(self.lista_sin_cuenta,
                         text="Todos los empleados tienen cuenta.", text_color="gray").pack(pady=20)
            return

        for empleado in sin_cuenta:
            fila = ctk.CTkFrame(self.lista_sin_cuenta)
            fila.pack(fill="x", pady=3)
            ctk.CTkLabel(fila, text=f"{empleado.nombre}  ·  {empleado.rut}").pack(
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
            self.lista_activas = lista
        else:
            self.lista_inactivas = lista

    def _cargar_cuentas(self, lista, solo_activos: bool) -> None:
        for widget in lista.winfo_children():
            widget.destroy()

        usuarios = usuario_repo.listar_todos()
        filtrados = [u for u in usuarios if u.activo == solo_activos
                     and u.rol.perfil_bd != "ti"]

        if not filtrados:
            msg = "No hay cuentas activas." if solo_activos else "No hay cuentas inactivas."
            ctk.CTkLabel(lista, text=msg, text_color="gray").pack(pady=20)
            return

        for usuario in filtrados:
            fila = ctk.CTkFrame(lista)
            fila.pack(fill="x", pady=3)
            ctk.CTkLabel(
                fila, text=f"{usuario.username}  ·  {usuario.rol.nombre}"
            ).pack(side="left", padx=10, pady=8)
            ctk.CTkButton(
                fila, text="Gestionar", width=100,
                command=lambda u=usuario: self._abrir_gestionar_cuenta(u)
            ).pack(side="right", padx=6)

    def _abrir_crear_usuario(self, empleado) -> None:
        CrearUsuarioView(self, empleado=empleado, on_guardado=self._recargar_todo)

    def _abrir_gestionar_cuenta(self, usuario) -> None:
        GestionarCuentaView(self, usuario=usuario, on_guardado=self._recargar_todo)

    def _recargar_todo(self) -> None:
        self._cargar_sin_cuenta()
        self._cargar_cuentas(self.lista_activas, solo_activos=True)
        self._cargar_cuentas(self.lista_inactivas, solo_activos=False)


def _dashboard():
    from gui.dashboard_view import DashboardView
    return DashboardView