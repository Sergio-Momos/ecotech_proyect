import customtkinter as ctk


def crear_encabezado(parent, app, titulo: str):
    """Construye el encabezado común y devuelve el contenedor para sus acciones."""
    encabezado = ctk.CTkFrame(parent, fg_color="transparent")
    encabezado.pack(fill="x", padx=20, pady=15)

    def volver():
        # La importación diferida evita el ciclo entre dashboard y sus vistas.
        from gui.dashboard_view import DashboardView
        app.navegar_a(DashboardView)

    ctk.CTkButton(
        encabezado, text="← Volver", width=90, command=volver,
    ).pack(side="left")
    ctk.CTkLabel(
        encabezado, text=titulo, font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(side="left", padx=20)
    return encabezado


def limpiar_contenedor(contenedor) -> None:
    """Destruye los elementos actuales antes de volver a llenar el contenedor."""
    for widget in contenedor.winfo_children():
        widget.destroy()
