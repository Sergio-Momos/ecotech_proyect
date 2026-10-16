import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import date

from mysql.connector import Error as ErrorBD

from models.informe import Informe
from repositorios import empleado_repo, departamento_repo, proyecto_repo, registro_tiempo_repo
from utils.fechas import leer_fecha_opcional
from gui.componentes import crear_encabezado
from utils.auditoria import accion, error as log_error


class InformesView(ctk.CTkFrame):
    TIPOS = {
        "Empleados": Informe._TIPO_EMPLEADOS,
        "Departamentos": Informe._TIPO_DEPARTAMENTOS,
        "Proyectos": Informe._TIPO_PROYECTOS,
        "Registros de horas": Informe._TIPO_REGISTROS_TIEMPO,
    }
    FORMATOS = {"pdf": ("PDF", ".pdf"), "excel": ("Excel", ".xlsx")}

    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app

        crear_encabezado(self, app, "Informes")

        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(pady=20)

        ctk.CTkLabel(cuerpo, text="Tipo de informe").pack(anchor="w")
        self.selector_tipo = ctk.CTkOptionMenu(cuerpo, values=list(self.TIPOS), width=300)
        self.selector_tipo.pack(pady=(0, 15))

        ctk.CTkLabel(cuerpo, text="Período (solo registros de horas, opcional)").pack(anchor="w")
        fechas = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fechas.pack(pady=(0, 20))
        self._entrada_desde = ctk.CTkEntry(fechas, placeholder_text="Desde AAAA-MM-DD", width=145)
        self._entrada_desde.pack(side="left", padx=(0, 10))
        self._entrada_hasta = ctk.CTkEntry(fechas, placeholder_text="Hasta AAAA-MM-DD", width=145)
        self._entrada_hasta.pack(side="left")

        for formato, (nombre, _) in self.FORMATOS.items():
            ctk.CTkButton(cuerpo, text=f"Descargar {nombre}", width=300,
                          command=lambda f=formato: self._exportar(f)).pack(pady=5)

    def _filas(self, tipo: str, desde, hasta) -> list[dict]:
        if tipo == Informe._TIPO_EMPLEADOS:
            return [{"Nombre": e._nombre, "RUT": e._rut, "Correo": e._correo, "Teléfono": e._telefono,
                     "Salario": e._salario, "Inicio contrato": e._fecha_inicio_contrato,
                     "Estado": "Activo" if e._activo else "Inactivo"}
                    for e in empleado_repo.listar_todos(incluir_inactivos=True)]
        if tipo == Informe._TIPO_DEPARTAMENTOS:
            return [{"Departamento": d._nombre, "Gerente": d._gerente._nombre,
                     "N° empleados": len(d._empleados)}
                    for d in departamento_repo.listar_todos()]
        if tipo == Informe._TIPO_PROYECTOS:
            return [{"Proyecto": p._nombre, "Descripción": p._descripcion, "Inicio": p._fecha_inicio,
                     "N° empleados": len(p._empleados), "Estado": "Activo" if p._activo else "Inactivo"}
                    for p in proyecto_repo.listar_todos(incluir_inactivos=True)]
        return [{"Fecha": r._fecha, "Empleado": r._empleado._nombre, "Proyecto": r._proyecto._nombre,
                 "Horas": r._horas_trabajadas, "Descripción": r._descripcion}
                for r in registro_tiempo_repo.listar(desde=desde, hasta=hasta)]

    def _exportar(self, formato: str) -> None:
        tipo = self.TIPOS[self.selector_tipo.get()]
        nombre, extension = self.FORMATOS[formato]
        usuario_id = self._app._usuario_actual._id

        try:
            desde = leer_fecha_opcional(self._entrada_desde.get(), "Desde")
            hasta = leer_fecha_opcional(self._entrada_hasta.get(), "Hasta")
            if desde and hasta and desde > hasta:
                raise ValueError("'Desde' no puede ser posterior a 'Hasta'.")
            informe = Informe(tipo)
            informe.generar_informe(self._filas(tipo, desde, hasta))
        except ValueError as e:
            messagebox.showerror("No se pudo generar el informe", str(e))
            return
        except (ConnectionError, ErrorBD) as e:
            log_error(usuario_id, "GENERAR_INFORME", str(e))
            messagebox.showerror("Error de base de datos", f"No se pudieron obtener los datos.\n{e}")
            return

        ruta = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[(nombre, f"*{extension}")],
            initialfile=f"informe_{tipo}_{date.today()}{extension}",
        )
        if not ruta:
            return

        try:
            getattr(informe, f"exportar_{formato}")(ruta)
        except OSError as e:
            log_error(usuario_id, "GENERAR_INFORME", str(e))
            messagebox.showerror("No se pudo guardar",
                                 f"Revisa que el archivo no esté abierto en otro programa.\n{e}")
            return

        accion(usuario_id, "GENERAR_INFORME", f"tipo={tipo}, formato={formato}")
        messagebox.showinfo("Informe listo", f"Se guardó en:\n{ruta}")
