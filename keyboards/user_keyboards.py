# telegram_subscription_bot/keyboards/user_keyboards.py
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_user_main_menu():
    """Retorna el teclado principal para usuarios"""
    builder = InlineKeyboardBuilder()
    
    buttons = [
        ("🔰 Estado de Suscripción", "subscription_status"),
        ("❓ Ayuda", "help")
    ]
    
    for text, callback_data in buttons:
        builder.button(text=text, callback_data=callback_data)
    
    builder.adjust(1)  # Una columna
    return builder.as_markup()