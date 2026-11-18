import customtkinter as ctk
import smtplib
from tkinter import messagebox

from mysql.connector import Error as ErrorBD

from repositorios import usuario_repo
from utils.correo import enviar_codigo_recuperacion
from utils.auditoria import accion, error as log_error


class CambiarPasswordView(ctk.CTkFrame):
    """Pantalla obligatoria al vencer la contraseña de acceso."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self._usuario = app._usuario_actual
        tarjeta = ctk.CTkFrame(self)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(tarjeta, text="Debes cambiar tu contraseña",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(padx=25, pady=(25, 10))
        ctk.CTkLabel(tarjeta, text="La contraseña vence cada 30 días.").pack(pady=(0, 12))
        self._nueva = ctk.CTkEntry(tarjeta, placeholder_text="Nueva contraseña", show="*", width=280)
        self._nueva.pack(pady=6)
        self._confirmar = ctk.CTkEntry(tarjeta, placeholder_text="Confirmar contraseña", show="*", width=280)
        self._confirmar.pack(pady=6)
        ctk.CTkButton(tarjeta, text="Guardar contraseña", command=self._guardar).pack(pady=20)

    def _guardar(self):
        if self._nueva.get() != self._confirmar.get():
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return
        try:
            usuario_repo.cambiar_password(self._usuario._id, self._nueva.get())
        except (ValueError, TypeError) as e:
            messagebox.showerror("Contraseña inválida", str(e))
            return
        except (ConnectionError, ErrorBD) as e:
            log_error(self._usuario._id, "CAMBIAR_PASSWORD", str(e))
            messagebox.showerror("Error de conexión", "No se pudo guardar la contraseña.")
            return
        accion(self._usuario._id, "CAMBIAR_PASSWORD")
        self._app.abrir_panel_principal()


class RecuperarPasswordView(ctk.CTkToplevel):
    """Solicita un código Gmail y permite establecer una contraseña nueva."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Recuperar contraseña")
        self.geometry("440x620")
        self.grab_set()
        self.resizable(False, False)
        tarjeta = ctk.CTkFrame(self, corner_radius=12)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(tarjeta, text="Recuperar cuenta EcoTech",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(padx=30, pady=(24, 8))
        ctk.CTkLabel(
            tarjeta, text="Ingresa tus datos registrados para recibir un código.",
            text_color="gray",
        ).pack(padx=25, pady=(0, 12))
        self._nombre = ctk.CTkEntry(tarjeta, placeholder_text="Nombre completo", width=300)
        self._nombre.pack(pady=8)
        self._rut = ctk.CTkEntry(tarjeta, placeholder_text="RUT", width=300)
        self._rut.pack(pady=8)
        self._correo = ctk.CTkEntry(tarjeta, placeholder_text="Correo registrado", width=300)
        self._correo.pack(pady=8)
        ctk.CTkButton(tarjeta, text="Enviar código", width=300, command=self._enviar).pack(pady=(8, 12))
        self._codigo = ctk.CTkEntry(tarjeta, placeholder_text="Código de 6 dígitos", width=300)
        self._codigo.pack(pady=8)
        self._nueva = ctk.CTkEntry(tarjeta, placeholder_text="Nueva contraseña", show="*", width=300)
        self._nueva.pack(pady=8)
        self._confirmar = ctk.CTkEntry(tarjeta, placeholder_text="Confirmar contraseña", show="*", width=300)
        self._confirmar.pack(pady=8)
        ctk.CTkButton(tarjeta, text="Cambiar contraseña", width=300, command=self._cambiar).pack(pady=(12, 24))

    def _enviar(self):
        correo = self._correo.get().strip()
        try:
            resultado = usuario_repo.solicitar_recuperacion_password(
                self._nombre.get(), self._rut.get(), correo
            )
            if not resultado:
                messagebox.showerror(
                    "Datos no coinciden",
                    "El nombre, RUT o correo ingresado no coincide con una cuenta activa. "
                    "Revisa los datos e inténtalo nuevamente.",
                )
                return
            enviar_codigo_recuperacion(*resultado)
            messagebox.showinfo("Solicitud recibida",
                "Si el correo corresponde a una cuenta activa, recibirás un código. Revisa tu bandeja y spam.")
        except (ConnectionError, ErrorBD, RuntimeError, OSError, smtplib.SMTPException) as e:
            messagebox.showerror("No se pudo enviar", str(e))

    def _cambiar(self):
        if self._nueva.get() != self._confirmar.get():
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return
        try:
            usuario_repo.recuperar_password(
                self._correo.get(), self._codigo.get(), self._nueva.get()
            )
        except (ValueError, TypeError) as e:
            messagebox.showerror("No se pudo cambiar", str(e))
            return
        except (ConnectionError, ErrorBD) as e:
            messagebox.showerror("Error de conexión", str(e))
            return
        messagebox.showinfo("Contraseña actualizada", "Ya puedes iniciar sesión con tu nueva contraseña.")
        self.destroy()
