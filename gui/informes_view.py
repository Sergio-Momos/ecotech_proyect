import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime, date
 
from mysql.connector import Error as ErrorBD
 
from models.informe import Informe
from repositorios import empleado_repo, departamento_repo, proyecto_repo, registro_tiempo_repo
from utils.auditoria import accion, error as log_error
 
 
class InformesView(ctk.CTkFrame):
    TIPOS = {
        "Empleados": Informe.TIPO_EMPLEADOS,
        "Departamentos": Informe.TIPO_DEPARTAMENTOS,
        "Proyectos": Informe.TIPO_PROYECTOS,
        "Registros de horas": Informe.TIPO_REGISTROS_TIEMPO,
    }
    FORMATOS = {"pdf": ("PDF", ".pdf"), "excel": ("Excel", ".xlsx")}
 
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
 
        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(encabezado, text="← Volver", width=90,
                      command=lambda: app.navegar_a(_dashboard())).pack(side="left")
        ctk.CTkLabel(encabezado, text="Informes",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)
 
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(pady=20)
 
        ctk.CTkLabel(cuerpo, text="Tipo de informe").pack(anchor="w")
        self.selector_tipo = ctk.CTkOptionMenu(cuerpo, values=list(self.TIPOS), width=300)
        self.selector_tipo.pack(pady=(0, 15))
 
        ctk.CTkLabel(cuerpo, text="Período (solo registros de horas, opcional)").pack(anchor="w")
        fechas = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fechas.pack(pady=(0, 20))
        self.entrada_desde = ctk.CTkEntry(fechas, placeholder_text="Desde AAAA-MM-DD", width=145)
        self.entrada_desde.pack(side="left", padx=(0, 10))
        self.entrada_hasta = ctk.CTkEntry(fechas, placeholder_text="Hasta AAAA-MM-DD", width=145)
        self.entrada_hasta.pack(side="left")
 
        for formato, (nombre, _) in self.FORMATOS.items():
            ctk.CTkButton(cuerpo, text=f"Descargar {nombre}", width=300,
                          command=lambda f=formato: self._exportar(f)).pack(pady=5)
 
    def _leer_fecha(self, entrada, nombre: str):
        texto = entrada.get().strip()
        if not texto:
            return None
        try:
            return datetime.strptime(texto, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"La fecha '{nombre}' debe tener el formato AAAA-MM-DD.") from None
 
    def _filas(self, tipo: str, desde, hasta) -> list[dict]:
        if tipo == Informe.TIPO_EMPLEADOS:
            return [{"Nombre": e.nombre, "RUT": e.rut, "Correo": e.correo, "Teléfono": e.telefono,
                     "Salario": e.salario, "Inicio contrato": e.fecha_inicio_contrato,
                     "Estado": "Activo" if e.activo else "Inactivo"}
                    for e in empleado_repo.listar_todos(incluir_inactivos=True)]
        if tipo == Informe.TIPO_DEPARTAMENTOS:
            return [{"Departamento": d.nombre, "Gerente": d.gerente.nombre,
                     "N° empleados": len(d.empleados)}
                    for d in departamento_repo.listar_todos()]
        if tipo == Informe.TIPO_PROYECTOS:
            return [{"Proyecto": p.nombre, "Descripción": p.descripcion, "Inicio": p.fecha_inicio,
                     "N° empleados": len(p.empleados), "Estado": "Activo" if p.activo else "Inactivo"}
                    for p in proyecto_repo.listar_todos(incluir_inactivos=True)]
        return [{"Fecha": r.fecha, "Empleado": r.empleado.nombre, "Proyecto": r.proyecto.nombre,
                 "Horas": r.horas_trabajadas, "Descripción": r.descripcion}
                for r in registro_tiempo_repo.listar(desde=desde, hasta=hasta)]
 
    def _exportar(self, formato: str) -> None:
        tipo = self.TIPOS[self.selector_tipo.get()]
        nombre, extension = self.FORMATOS[formato]
        usuario_id = self.app.usuario_actual.id
 
        try:
            desde = self._leer_fecha(self.entrada_desde, "Desde")
            hasta = self._leer_fecha(self.entrada_hasta, "Hasta")
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
 
 
def _dashboard():
    from gui.dashboard_view import DashboardView
    return DashboardView