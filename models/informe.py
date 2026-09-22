from datetime import date
from typing import Any

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


class Informe:
    TIPO_EMPLEADOS = "empleados"
    TIPO_DEPARTAMENTOS = "departamentos"
    TIPO_PROYECTOS = "proyectos"
    TIPO_REGISTROS_TIEMPO = "registros_tiempo"

    TIPOS_VALIDOS = frozenset(
        {TIPO_EMPLEADOS, TIPO_DEPARTAMENTOS, TIPO_PROYECTOS, TIPO_REGISTROS_TIEMPO}
    )

    def __init__(self, tipo: str) -> None:
        self.tipo = tipo
        self._fecha_generacion = date.today()  # se autoasigna, no la pasa nadie
        self._contenido: list[dict[str, Any]] = []
        self._formato = None  # se fija recién al exportar

    @property
    def tipo(self) -> str:
        return self._tipo

    @tipo.setter
    def tipo(self, valor: str) -> None:
        if valor not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo de informe inválido: {valor}")
        self._tipo = valor

    @property
    def fecha_generacion(self) -> date:
        return self._fecha_generacion

    @property
    def formato(self) -> str:
        return self._formato

    def generar_informe(self, filas: list[dict[str, Any]]) -> None:
        # `filas` ya viene aplanado a valores simples por quien llama a
        # este método — Informe nunca ve ni retiene un Empleado,
        # Departamento, Proyecto ni RegistroTiempo real.
        if not filas:
            raise ValueError("No hay datos para generar el informe.")
        self._contenido = filas

    def exportar_pdf(self, ruta: str) -> str:
        if not self._contenido:
            raise ValueError("Debe generar el informe antes de exportarlo.")
        columnas = list(self._contenido[0].keys())
        filas_tabla = [columnas] + [
            [str(fila[c]) for c in columnas] for fila in self._contenido
        ]
        doc = SimpleDocTemplate(ruta, pagesize=letter)
        tabla = Table(filas_tabla)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        doc.build([tabla])
        self._formato = "pdf"
        return ruta

    def exportar_excel(self, ruta: str) -> str:
        if not self._contenido:
            raise ValueError("Debe generar el informe antes de exportarlo.")
        wb = Workbook()
        hoja = wb.active
        columnas = list(self._contenido[0].keys())
        hoja.append(columnas)
        for fila in self._contenido:
            hoja.append([fila[c] for c in columnas])
        wb.save(ruta)
        self._formato = "excel"
        return ruta