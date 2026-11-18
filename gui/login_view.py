import customtkinter as ctk
from tkinter import messagebox

from repositorios import usuario_repo
from utils.auditoria import error as log_error
from mysql.connector import Error as ErrorBD

class LoginView(ctk.CTkFrame):
    """Pantalla que solicita credenciales y valida el acceso mediante el DAO."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app

        tarjeta = ctk.CTkFrame(self, corner_radius=12)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")
        #1 titulo principal
        self._lbl_titulo = ctk.CTkLabel(tarjeta, text="EcoTech Solutions", font=ctk.CTkFont(size=22, weight="bold"))
        self._lbl_titulo.pack(pady=(30, 20), padx=30)

        # 2. Campo para Usuario
        self._entry_usuario = ctk.CTkEntry(
            tarjeta,
            placeholder_text="Nombre de usuario",
            width=250
        )
        self._entry_usuario.pack(pady=10, padx=20)

        # 3. Campo para Contraseña
        self._password_visible = False
        ctk.CTkLabel(tarjeta, text="Contraseña").pack(pady=(10, 0))
        self._entry_password = ctk.CTkEntry(
            tarjeta,
            show="*",
            width=250
        )
        self._entry_password.pack(pady=10, padx=20)
        self._entry_password.bind("<Return>", lambda event: self._intentar_login())

        self._btn_mostrar_password = ctk.CTkButton(
            tarjeta,
            text="Mostrar contraseña",
            command=self._alternar_visibilidad_password,
            width=250
        )
        self._btn_mostrar_password.pack(pady=(0, 10), padx=20)

        # 4. Botón de Ingreso
        self._btn_ingresar = ctk.CTkButton(
            tarjeta,
            text="Ingresar",
            command=self._intentar_login,
            width=250
        )
        self._btn_ingresar.pack(pady=(20, 30), padx=20)

        self._btn_recuperar = ctk.CTkButton(
            tarjeta, text="Olvidé mi contraseña", width=250,
            fg_color="transparent", text_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
            hover_color=("#DCEFE6", "#244A39"), command=self._abrir_recuperacion,
        )
        self._btn_recuperar.pack(pady=(0, 20), padx=20)

    def _abrir_recuperacion(self) -> None:
        from gui.password_view import RecuperarPasswordView
        RecuperarPasswordView(self)

    def _alternar_visibilidad_password(self) -> None:
        self._password_visible = not self._password_visible
        self._entry_password.configure(show="" if self._password_visible else "*")
        self._btn_mostrar_password.configure(
            text="Ocultar contraseña" if self._password_visible else "Mostrar contraseña"
        )
        self._entry_password.focus_set()

    def _intentar_login(self) -> None:
        """Busca la cuenta activa, verifica la contraseña y notifica a App."""
        username = self._entry_usuario.get().strip()
        try:
            usuario = usuario_repo.buscar_por_username_activo(username)
        except (ConnectionError, ErrorBD) as e:
            log_error(0, "LOGIN", str(e))
            messagebox.showerror("Error de conexión", "No se pudo consultar el usuario. Inténtalo nuevamente.")
            return
        password = self._entry_password.get()
        if usuario is None or not usuario.verificar_password(password):
            log_error(0, "LOGIN", f"intento fallido: {username}")
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
            self._entry_password.delete(0, "end")
            self._password_visible = False
            self._entry_password.configure(show="*")
            self._btn_mostrar_password.configure(text="Mostrar contraseña")
            self._entry_password.focus_set()
            return
        from models.seguridad import Seguridad
        if Seguridad.necesita_rehash(usuario._valor_password):
            try:
                usuario_repo.actualizar_hash_password(
                    usuario, Seguridad.hashear_password(password)
                )
            except (ConnectionError, ErrorBD) as e:
                log_error(0, "LOGIN", f"no se pudo actualizar el hash de {username}: {e}")
                messagebox.showerror(
                    "Error de conexión",
                    "No se pudo actualizar la seguridad de la cuenta. Inténtalo nuevamente.",
                )
                return
        try:
            password_vencida = usuario_repo.password_vencida(usuario._id)
        except (ConnectionError, ErrorBD) as e:
            log_error(0, "LOGIN", f"no se pudo revisar vencimiento: {e}")
            messagebox.showerror("Error de conexión", "No se pudo validar el vencimiento de la contraseña.")
            return
        try:
            self._app.iniciar_sesion_exitosa(usuario, password_vencida=password_vencida)
        except ValueError as e:
            messagebox.showerror("Error de configuración", str(e))
