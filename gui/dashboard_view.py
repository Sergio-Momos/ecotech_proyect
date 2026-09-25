import customtkinter as ctk
from tkinter import messagebox

from models.rol import Rol
from gui.empleados_view import EmpleadosView
from gui.departamentos_view import DepartamentosView
from gui.proyectos_view import ProyectosView
from gui.registros_view import RegistrosView
from gui.ti_view import TiView
class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app
        usuario = app.usuario_actual
        rol = usuario.rol

        ctk.CTkLabel(
            self,
            text=f"Bienvenido, {usuario.username}",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(30, 5))

        ctk.CTkLabel(
            self,
            text=f"Rol: {rol.nombre}",
            text_color="gray",
        ).pack(pady=(0, 30))

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(pady=10)

        opciones = [
            (Rol.CREAR_EMPLEADOS, "Gestionar Empleados", lambda: app.navegar_a(EmpleadosView)),
            (Rol.ASIGNAR_EMPLEADOS_DEPARTAMENTO, "Gestionar Departamentos", lambda: app.navegar_a(DepartamentosView)),
            (Rol.ASIGNAR_EMPLEADOS_PROYECTO, "Gestionar Proyectos", lambda: app.navegar_a(ProyectosView)),
            (Rol.LEER_REGISTROS_TODOS, "Ver todos los registros de horas", lambda: app.navegar_a(RegistrosView)),
            (Rol.LEER_REGISTROS_PROPIOS, "Mis horas trabajadas", lambda: app.navegar_a(RegistrosView)),
            (Rol.CREAR_USUARIOS, "Gestión de usuarios", lambda: app.navegar_a(TiView)),
        ]

        for permiso, texto, comando in opciones:
            if rol.tiene_permiso(permiso):
                ctk.CTkButton(
                    botones,
                    text=texto,
                    width=220,
                    command=comando,
                ).pack(pady=8)

        ctk.CTkButton(
            self,
            text="Cerrar sesión",
            fg_color="transparent",
            border_width=1,
            command=app.cerrar_sesion,
        ).pack(pady=(30, 10))

    def _proximamente(self) -> None:
        messagebox.showinfo(
            "EcoTech Solutions",
            "Esta sección todavía no está construida.",
        )