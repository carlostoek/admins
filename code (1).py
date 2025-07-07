
# telegram_subscription_bot/config.py
from dotenv import load_dotenv
import os

load_dotenv()

# Bot y canales
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
FREE_CHANNEL_ID = os.getenv("FREE_CHANNEL_ID")
VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID")

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.sqlite3")

# Mensajes predeterminados
DEFAULT_WELCOME_MESSAGE = "¡Bienvenido al bot de suscripciones!"
DEFAULT_RENEWAL_MESSAGE = "Tu suscripción VIP está a punto de vencer. ¡Renuévala ahora!"
DEFAULT_CANCELLATION_MESSAGE = "Tu suscripción VIP ha sido cancelada."

# Configuración del acceso libre al canal gratuito (True/False)
FREE_CHANNEL_OPEN_ACCESS = os.getenv("FREE_CHANNEL_OPEN_ACCESS", "True").lower() == "true"

