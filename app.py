#!/usr/bin/env python3

"""Lanzador de la aplicación con el Python compatible del proyecto."""

import os
import sys
from pathlib import Path


def _usar_python_del_proyecto() -> None:
    """Reinicia con el entorno local compatible cuando se ejecuta con otro Python."""
    raiz = Path(__file__).resolve().parent
    entorno = raiz / ".venv314" / "bin" / "python"
    if entorno.is_file() and Path(sys.prefix).resolve() != (raiz / ".venv314").resolve():
        os.execv(str(entorno), [str(entorno), __file__, *sys.argv[1:]])


_usar_python_del_proyecto()

import customtkinter as ctk

from gui.login_view import LoginView
from gui.dashboard_view import DashboardView
from database.conexion import establecer_perfil_activo, limpiar_perfil_activo
from utils.auditoria import accion, error

class App(ctk.CTk):
    """Ventana raíz: coordina navegación y estado de la sesión actual."""
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
        """Muestra una pantalla nueva y destruye la anterior."""
        nuevo = clase_frame(self._contenedor, self)
        nuevo.pack(fill="both", expand=True)
        if self._frame_actual is not None:
            self._frame_actual.destroy()
        self._frame_actual = nuevo

    def iniciar_sesion_exitosa(self, usuario, password_vencida: bool = False) -> None:
        """Guarda el usuario y obliga a renovar su contraseña si venció."""
        self._usuario_actual = usuario
        establecer_perfil_activo(usuario._rol._perfil_bd)
        accion(usuario._id, "LOGIN_EXITOSO")
        if password_vencida:
            from gui.password_view import CambiarPasswordView
            self.navegar_a(CambiarPasswordView)
        else:
            self.abrir_panel_principal()

    def abrir_panel_principal(self) -> None:
        self.navegar_a(DashboardView)

    def cerrar_sesion(self) -> None:
        """Registra el cierre, limpia la sesión y regresa al login."""
        if self._usuario_actual:
            accion(self._usuario_actual._id, "LOGOUT")
        self._usuario_actual = None
        limpiar_perfil_activo()
        self.navegar_a(LoginView)


if __name__ == "__main__":
    App().mainloop()
