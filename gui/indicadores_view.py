import customtkinter as ctk
from tkinter import messagebox

from integraciones.uf_api import ErrorIndicadorUF, actualizar_serie_uf
from repositorios import indicador_repo
from utils.auditoria import accion, error as log_error


class IndicadoresView(ctk.CTkFrame):
    """Consulta y actualización de indicadores económicos guardados."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self._usuario_id = app._usuario_actual._id

        ctk.CTkLabel(
            self, text="Indicadores económicos",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 6))
        ctk.CTkLabel(self, text="UF diaria · API: indicadores.cl · Datos: SII").pack(pady=(0, 10))
        ctk.CTkButton(
            self, text="Actualizar UF desde la API", command=self._actualizar,
        ).pack(pady=(0, 12))

        self._lista = ctk.CTkScrollableFrame(self, label_text="Últimos valores guardados")
        self._lista.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        ctk.CTkButton(self, text="Volver", command=self._volver).pack(pady=(0, 18))
        self._cargar()

    def _volver(self) -> None:
        from gui.dashboard_view import DashboardView
        self._app.navegar_a(DashboardView)

    def _cargar(self) -> None:
        for widget in self._lista.winfo_children():
            widget.destroy()
        try:
            valores = indicador_repo.listar("uf", 30)
        except Exception as exc:
            log_error(self._usuario_id, "LEER_INDICADORES", str(exc))
            ctk.CTkLabel(self._lista, text="No se pudieron cargar los indicadores guardados.").pack(pady=12)
            return

        if not valores:
            ctk.CTkLabel(self._lista, text="Aún no hay datos. Usa el botón para consultar la API.").pack(pady=12)
            return
        for indicador in valores:
            fecha = indicador["fecha"].strftime("%d-%m-%Y")
            valor = f"${indicador['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            ctk.CTkLabel(
                self._lista, text=f"{fecha}    {valor} {indicador['unidad_medida']}",
                anchor="w",
            ).pack(fill="x", padx=12, pady=4)

    def _actualizar(self) -> None:
        try:
            cantidad = actualizar_serie_uf()
        except (ErrorIndicadorUF, ConnectionError, OSError, ValueError) as exc:
            log_error(self._usuario_id, "ACTUALIZAR_UF_API", str(exc))
            messagebox.showerror("No se pudo actualizar la UF", str(exc))
            return
        except Exception as exc:
            log_error(self._usuario_id, "ACTUALIZAR_UF_API", str(exc))
            messagebox.showerror("Error al guardar la UF", "No se pudieron guardar los datos recibidos.")
            return

        accion(self._usuario_id, "ACTUALIZAR_UF_API", f"registros={cantidad}")
        self._cargar()
        messagebox.showinfo("UF actualizada", f"Se guardaron {cantidad} valores diarios de UF.")
