import customtkinter as ctk

from gui.login_view import LoginView
from gui.dashboard_view import DashboardView
from database.conexion import establecer_perfil_activo, limpiar_perfil_activo
from utils.auditoria import accion, error

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self.title("EcoTech Solutions — Gestión RRHH")
        self.geometry("900x600")

        self._usuario_actual = None

        self._contenedor = ctk.CTkFrame(self)
        self._contenedor.pack(fill="both", expand=True)
        self._frame_actual = None

        self.navegar_a(LoginView)

    def navegar_a(self, clase_frame) -> None:
        nuevo = clase_frame(self._contenedor, self)
        nuevo.pack(fill="both", expand=True)
        if self._frame_actual is not None:
            self._frame_actual.destroy()
        self._frame_actual = nuevo

    def iniciar_sesion_exitosa(self, usuario) -> None:
        self._usuario_actual = usuario
        establecer_perfil_activo(usuario._rol._perfil_bd)
        accion(usuario._id, "LOGIN_EXITOSO")
        self.navegar_a(DashboardView)

    def cerrar_sesion(self) -> None:
        if self._usuario_actual:
            accion(self._usuario_actual._id, "LOGOUT")
        self._usuario_actual = None
        limpiar_perfil_activo()
        self.navegar_a(LoginView)


if __name__ == "__main__":
    App().mainloop()
