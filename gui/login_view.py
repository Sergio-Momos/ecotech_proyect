import customtkinter as ctk
from tkinter import messagebox

from repositorios import usuario_repo
from utils.auditoria import error as log_error
from mysql.connector import Error as ErrorBD

class LoginView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app

        tarjeta = ctk.CTkFrame(self)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")
        #1 titulo principal
        self._lbl_titulo = ctk.CTkLabel(tarjeta, text="EcoTech Solutions", font=ctk.CTkFont(size=22, weight="bold"))
        self._lbl_titulo.pack(pady=(30, 20), padx=30)

        # 2. Campo para Usuario
        self._entry_usuario = ctk.CTkEntry(
            self,
            placeholder_text="Nombre de usuario",
            width=250
        )
        self._entry_usuario.pack(pady=10, padx=20)

        # 3. Campo para Contraseña
        self._password_visible = False
        ctk.CTkLabel(self, text="Contraseña").pack(pady=(10, 0))
        self._entry_password = ctk.CTkEntry(
            self,
            show="*",
            width=250
        )
        self._entry_password.pack(pady=10, padx=20)
        self._entry_password.bind("<Return>", lambda event: self._intentar_login())

        self._btn_mostrar_password = ctk.CTkButton(
            self,
            text="Mostrar contraseña",
            command=self._alternar_visibilidad_password,
            width=250
        )
        self._btn_mostrar_password.pack(pady=(0, 10), padx=20)

        # 4. Botón de Ingreso
        self._btn_ingresar = ctk.CTkButton(
            self,
            text="Ingresar",
            command=self._intentar_login,
            width=250
        )
        self._btn_ingresar.pack(pady=(20, 30), padx=20)

    def _alternar_visibilidad_password(self) -> None:
        self._password_visible = not self._password_visible
        self._entry_password.configure(show="" if self._password_visible else "*")
        self._btn_mostrar_password.configure(
            text="Ocultar contraseña" if self._password_visible else "Mostrar contraseña"
        )
        self._entry_password.focus_set()

    def _intentar_login(self) -> None:
        username = self._entry_usuario.get().strip()
        try:
            usuario = usuario_repo.buscar_por_username_activo(username)
        except (ConnectionError, ErrorBD) as e:
            log_error(0, "LOGIN", str(e))
            messagebox.showerror("Error de conexión", "No se pudo consultar el usuario. Inténtalo nuevamente.")
            return
        if usuario is None or not usuario.verificar_password(self._entry_password.get()):
            log_error(0, "LOGIN", f"intento fallido: {username}")
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
            self._entry_password.delete(0, "end")
            self._password_visible = False
            self._entry_password.configure(show="*")
            self._btn_mostrar_password.configure(text="Mostrar contraseña")
            self._entry_password.focus_set()
            return
        try:
            self._app.iniciar_sesion_exitosa(usuario)
        except ValueError as e:
            messagebox.showerror("Error de configuración", str(e))
