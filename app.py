import customtkinter as ctk

from gui.login_view import LoginView
from gui.dashboard_view import DashboardView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self.title("EcoTech Solutions — Gestión RRHH")
        self.geometry("900x600")

        self.usuario_actual = None

        self._contenedor = ctk.CTkFrame(self)
        self._contenedor.pack(fill="both", expand=True)
        self._frame_actual = None

        self.navegar_a(LoginView)

    def navegar_a(self, clase_frame) -> None:
        if self._frame_actual is not None:
            self._frame_actual.destroy()
        nuevo = clase_frame(self._contenedor, self)
        nuevo.pack(fill="both", expand=True)
        self._frame_actual = nuevo

    def iniciar_sesion_exitosa(self, usuario) -> None:
        self.usuario_actual = usuario
        self.navegar_a(DashboardView)

    def cerrar_sesion(self) -> None:
        self.usuario_actual = None
        self.navegar_a(LoginView)


if __name__ == "__main__":
    App().mainloop()