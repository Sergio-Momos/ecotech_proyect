"""Envío de mensajes de recuperación mediante Gmail API y OAuth de escritorio."""

import base64
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import GMAIL_ADDRESS


_BASE = Path(__file__).resolve().parent.parent
_CREDENTIALS = _BASE / "credentials.json"
_TOKEN = _BASE / "token.json"
_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _credenciales_gmail() -> Credentials:
    if not GMAIL_ADDRESS:
        raise RuntimeError("Falta configurar GMAIL_ADDRESS en .env.")
    if not _CREDENTIALS.is_file():
        raise RuntimeError(
            "No se encontró credentials.json. Descarga las credenciales OAuth de escritorio "
            "de Google Cloud y guárdalas en la carpeta principal del proyecto."
        )

    credenciales = None
    if _TOKEN.is_file():
        credenciales = Credentials.from_authorized_user_file(str(_TOKEN), _SCOPES)
    if credenciales and credenciales.expired and credenciales.refresh_token:
        credenciales.refresh(Request())
    if not credenciales or not credenciales.valid:
        flujo = InstalledAppFlow.from_client_secrets_file(str(_CREDENTIALS), _SCOPES)
        credenciales = flujo.run_local_server(port=0)
    _TOKEN.write_text(credenciales.to_json(), encoding="utf-8")
    return credenciales


def enviar_codigo_recuperacion(destinatario: str, codigo: str) -> None:
    """Autoriza Gmail una vez en el navegador y envía el código por HTTPS."""

    mensaje = EmailMessage()
    mensaje["Subject"] = "Código para recuperar tu cuenta EcoTech"
    mensaje["From"] = GMAIL_ADDRESS
    mensaje["To"] = destinatario
    mensaje.set_content(
        "Usa este código para recuperar tu cuenta EcoTech: " + codigo +
        "\n\nEl código vence en 10 minutos. Si no solicitaste el cambio, ignora este mensaje."
    )

    raw = base64.urlsafe_b64encode(mensaje.as_bytes()).decode("ascii")
    try:
        servicio = build("gmail", "v1", credentials=_credenciales_gmail(), cache_discovery=False)
        servicio.users().messages().send(userId="me", body={"raw": raw}).execute()
    except HttpError as e:
        raise RuntimeError(f"Gmail API rechazó el envío: {e}") from e
    except Exception as e:
        raise RuntimeError(f"No se pudo conectar con Gmail API: {e}") from e
