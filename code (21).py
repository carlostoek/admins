# telegram_subscription_bot/utils/helpers.py
import datetime
import json
from typing import List, Dict, Any

def format_datetime(dt: datetime.datetime) -> str:
    """Formatea una fecha y hora en un formato legible"""
    return dt.strftime("%d/%m/%Y %H:%M")

def parse_buttons_json(buttons_json: str) -> List[List[Dict[str, Any]]]:
    """Convierte un JSON de botones en una estructura utilizable por aiogram"""
    try:
        return json.loads(buttons_json)
    except:
        return []

def generate_crontab_from_recurrence(recurrence_type: str, day_of_week: int = None, 
                                    hour: int = 0, minute: int = 0) -> str:
    """
    Genera una expresión crontab a partir de un tipo de recurrencia
    
    Tipos de recurrencia:
    - daily: Diariamente
    - weekly: Semanalmente (requiere day_of_week, 0=lunes, 6=domingo)
    - monthly: Mensualmente (mismo día del mes)
    """
    if recurrence_type == "daily":
        return f"{minute} {hour} * * *"
    elif recurrence_type == "weekly" and day_of_week is not None:
        return f"{minute} {hour} * * {day_of_week}"
    elif recurrence_type == "monthly":
        return f"{minute} {hour} 1 * *"
    else:
        # Predeterminado: diario a medianoche
        return "0 0 * * *"