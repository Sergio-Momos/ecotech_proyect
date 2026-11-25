PATRON_CORREO = r"^[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}$"
PATRON_NOMBRE = r"^[a-zA-ZáéíóúÁÉÍÓÚÑñ\s']+$"
PATRON_TELEFONO = r"^\d{8,9}$"
PATRON_RUT = r"^\d{7,8}[\dK]$"
PATRON_USERNAME = r"^(?!\.)(?!.*\.\.)[a-zA-Z0-9.]{4,20}(?<!\.)$"
PATRON_PASSWORD = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$" #NOSONAR

ERROR_CORREO = "El correo tiene un formato inválido."
ERROR_SOLO_LETRAS = "El nombre debe contener solo letras."
ERROR_TELEFONO = "El teléfono debe tener 8 o 9 números."
ERROR_RUT = "El RUT es inválido; revisa su formato y dígito verificador."
ERROR_USERNAME = (
    "El username debe tener entre 4 y 20 caracteres alfanuméricos o puntos, "
    "sin iniciar, terminar ni repetir puntos."
)
ERROR_PASSWORD = "La contraseña debe tener mínimo 8 caracteres, una mayúscula, una minúscula, un número y un símbolo especial."  # NOSONAR
