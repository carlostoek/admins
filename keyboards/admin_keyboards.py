# telegram_subscription_bot/keyboards/admin_keyboards.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import SubscriptionPlan

def get_admin_main_menu():
    """Retorna el teclado principal para administradores"""
    builder = InlineKeyboardBuilder()
    
    buttons = [
        ("📝 Configurar Tarifas", "config_tariffs"),
        ("🔗 Generar Enlace", "generate_link"),
        ("👥 Gestionar Usuarios VIP", "manage_vip_users"),
        ("📢 Configurar Canales", "channel_config"),
        ("✉️ Enviar Mensaje", "send_message"),
        ("📊 Estadísticas", "statistics")
    ]
    
    for text, callback_data in buttons:
        builder.button(text=text, callback_data=callback_data)
    
    builder.adjust(1)  # Una columna
    return builder.as_markup()

def get_tariff_duration_keyboard():
    """Retorna el teclado para seleccionar duración de tarifa"""
    builder = InlineKeyboardBuilder()
    
    buttons = [
        ("1 día", "duration_1d"),
        ("1 semana", "duration_1w"),
        ("2 semanas", "duration_2w"),
        ("1 mes", "duration_1m"),
        ("Permanente", "duration_permanent"),
        ("❌ Cancelar", "cancel")
    ]
    
    for text, callback_data in buttons:
        builder.button(text=text, callback_data=callback_data)
    
    builder.adjust(1)  # Una columna
    return builder.as_markup()

def get_confirm_tariff_keyboard():
    """Retorna el teclado para confirmar la tarifa"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Confirmar", callback_data="confirm_tariff")
    builder.button(text="❌ Cancelar", callback_data="cancel_tariff")
    
    builder.adjust(2)  # Dos columnas
    return builder.as_markup()

def get_subscription_plans_keyboard(plans):
    """Retorna el teclado con los planes de suscripción disponibles"""
    builder = InlineKeyboardBuilder()
    
    for plan in plans:
        # Determinar texto de duración
        if plan.is_permanent:
            duration_text = "Permanente"
        elif plan.duration_days == 1:
            duration_text = "1 día"
        elif plan.duration_days == 7:
            duration_text = "1 semana"
        elif plan.duration_days == 14:
            duration_text = "2 semanas"
        elif plan.duration_days == 30:
            duration_text = "1 mes"
        else:
            duration_text = f"{plan.duration_days} días"
        
        button_text = f"{plan.name} ({duration_text}) - ${plan.price}"
        builder.button(text=button_text, callback_data=f"plan_{plan.id}")
    
    builder.button(text="❌ Cancelar", callback_data="cancel")
    
    builder.adjust(1)  # Una columna
    return builder.as_markup()

def get_channel_config_keyboard():
    """Retorna el teclado para configuración de canales"""
    builder = InlineKeyboardBuilder()
    
    buttons = [
        ("📢 Configurar Canal Gratuito", "channel_free"),
        ("🔒 Configurar Canal VIP", "channel_vip"),
        ("🔙 Volver", "back_to_admin")
    ]
    
    for text, callback_data in buttons:
        builder.button(text=text, callback_data=callback_data)
    
    builder.adjust(1)  # Una columna
    return builder.as_markup()