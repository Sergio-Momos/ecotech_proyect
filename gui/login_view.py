import customtkinter as ctk
from tkinter import messagebox

from repositorios import usuario_repo


class LoginView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        tarjeta = ctk.CTkFrame(self)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")
        #1 titulo principal
        self.lbl_titulo = ctk.CTkLabel(tarjeta, text="EcoTech Solutions", font=ctk.CTkFont(size=22, weight="bold"))
        self.lbl_titulo.pack(pady=(30, 20), padx=30)

        # 2. Campo para Usuario
        self.entry_usuario = ctk.CTkEntry(
            self, 
            placeholder_text="Nombre de usuario",
            width=250
        )
        self.entry_usuario.pack(pady=10, padx=20)

        # 3. Campo para Contraseña
        self.entry_password = ctk.CTkEntry(
            self, 
            placeholder_text="Contraseña", 
            show="*",
            width=250
        )
        self.entry_password.pack(pady=10, padx=20)
        self.entry_password.bind("<Return>", lambda event: self._intentar_login())

        # 4. Botón de Ingreso
        self.btn_ingresar = ctk.CTkButton(
            self, 
            text="Ingresar", 
            command=self._intentar_login,
            width=250
        )
        self.btn_ingresar.pack(pady=(20, 30), padx=20)

    def _intentar_login(self) -> None:
        username = self.entry_usuario.get()
        password = self.entry_password.get()

        usuario = usuario_repo.buscar_por_username(username)
        if usuario is None or not usuario.verificar_password(password):
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
            self.entry_password.delete(0, "end")
            return

        try:
            self.app.iniciar_sesion_exitosa(usuario)
        except ValueError as e:
            messagebox.showerror("Error de configuración", str(e))

        self.app.iniciar_sesion_exitosa(usuario)