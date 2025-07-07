# telegram_subscription_bot/handlers/admin_handlers.py
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database.db import get_session
from database.models import User, SubscriptionPlan
from services.token_service import TokenService
from services.subscription_service import SubscriptionService
from services.scheduler_service import SchedulerService
from services.channel_service import ChannelService
from keyboards.admin_keyboards import (
    get_admin_main_menu, get_subscription_plans_keyboard,
    get_tariff_duration_keyboard, get_confirm_tariff_keyboard,
    get_channel_config_keyboard
)
from config import ADMIN_IDS, FREE_CHANNEL_ID, VIP_CHANNEL_ID

router = Router()

# FSM para configuración de tarifas
class TariffConfig(StatesGroup):
    selecting_duration = State()
    entering_price = State()
    entering_name = State()
    confirming = State()

# FSM para generar enlace
class GenerateLink(StatesGroup):
    selecting_plan = State()

# FSM para enviar mensaje
class SendMessage(StatesGroup):
    selecting_channel = State()
    entering_text = State()
    selecting_media = State()
    confirming = State()
    selecting_protection = State()
    selecting_buttons = State()
    entering_button_text = State()
    entering_button_url = State()
    scheduling = State()

# Filtro para administradores
def admin_filter(message: Message):
    return message.from_user.id in ADMIN_IDS

# Comandos administrativos
@router.message(Command("admin"), admin_filter)
async def admin_command(message: Message):
    await message.answer(
        "Panel de Administración",
        reply_markup=get_admin_main_menu()
    )

# Configuración de tarifas
@router.callback_query(F.data == "config_tariffs", StateFilter(None))
async def config_tariffs(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Selecciona la duración de la suscripción:",
        reply_markup=get_tariff_duration_keyboard()
    )
    await state.set_state(TariffConfig.selecting_duration)

@router.callback_query(StateFilter(TariffConfig.selecting_duration))
async def process_duration(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    duration_data = callback.data
    
    if duration_data == "cancel":
        await state.clear()
        await callback.message.answer("Configuración cancelada.")
        return
    
    # Guardar duración seleccionada
    duration_mapping = {
        "duration_1d": 1,
        "duration_1w": 7,
        "duration_2w": 14,
        "duration_1m": 30,
        "duration_permanent": -1  # Valor especial para suscripciones permanentes
    }
    
    duration_days = duration_mapping.get(duration_data)
    await state.update_data(duration_days=duration_days)
    
    # Solicitar precio
    await callback.message.answer("Ingresa el precio de la suscripción:")
    await state.set_state(TariffConfig.entering_price)

@router.message(StateFilter(TariffConfig.entering_price))
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip())
        if price < 0:
            await message.answer("El precio no puede ser negativo. Intenta nuevamente:")
            return
        
        await state.update_data(price=price)
        await message.answer("Ingresa un nombre para esta tarifa:")
        await state.set_state(TariffConfig.entering_name)
    except ValueError:
        await message.answer("Por favor, ingresa un número válido para el precio:")

@router.message(StateFilter(TariffConfig.entering_name))
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("El nombre no puede estar vacío. Intenta nuevamente:")
        return
    
    data = await state.get_data()
    data["name"] = name
    await state.update_data(data)
    
    # Mostrar resumen para confirmación
    duration_days = data["duration_days"]
    price = data["price"]
    
    if duration_days == -1:
        duration_text = "Permanente"
    elif duration_days == 1:
        duration_text = "1 día"
    elif duration_days == 7:
        duration_text = "1 semana"
    elif duration_days == 14:
        duration_text = "2 semanas"
    elif duration_days == 30:
        duration_text = "1 mes"
    else:
        duration_text = f"{duration_days} días"
    
    await message.answer(
        f"Resumen de la tarifa:\n\n"
        f"📝 Nombre: {name}\n"
        f"⏱️ Duración: {duration_text}\n"
        f"💰 Precio: {price}\n\n"
        f"¿Confirmas esta configuración?",
        reply_markup=get_confirm_tariff_keyboard()
    )
    await state.set_state(TariffConfig.confirming)

@router.callback_query(StateFilter(TariffConfig.confirming))
async def confirm_tariff(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    
    if callback.data == "confirm_tariff":
        data = await state.get_data()
        
        # Crear plan de suscripción
        is_permanent = data["duration_days"] == -1
        duration = 36500 if is_permanent else data["duration_days"]  # 100 años si es permanente
        
        plan = await SubscriptionService.create_subscription_plan(
            name=data["name"],
            duration_days=duration,
            price=data["price"],
            is_permanent=is_permanent
        )
        
        await callback.message.answer(f"✅ Tarifa '{data['name']}' creada exitosamente.")
    else:
        await callback.message.answer("❌ Configuración cancelada.")
    
    await state.clear()

# Generación de enlaces con token
@router.callback_query(F.data == "generate_link", StateFilter(None))
async def generate_link_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    # Obtener planes de suscripción
    plans = await SubscriptionService.get_subscription_plans()
    
    if not plans:
        await callback.message.answer("No hay planes de suscripción configurados. Primero debes crear al menos uno.")
        return
    
    await callback.message.answer(
        "Selecciona el plan para generar un enlace:",
        reply_markup=get_subscription_plans_keyboard(plans)
    )
    await state.set_state(GenerateLink.selecting_plan)

@router.callback_query(StateFilter(GenerateLink.selecting_plan))
async def generate_link_for_plan(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    
    if callback.data == "cancel":
        await state.clear()
        await callback.message.answer("Generación de enlace cancelada.")
        return
    
    # Extraer plan_id del callback
    plan_id = int(callback.data.split("_")[1])
    
    # Generar token
    token = await TokenService.generate_token(plan_id)
    
    if not token:
        await callback.message.answer("Error al generar el token. Inténtalo de nuevo.")
        await state.clear()
        return
    
    # Crear enlace con el token
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    link = f"https://t.me/{bot_username}?start={token.token}"
    
    # Obtener información del plan
    async with get_session() as session:
        result = await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
        plan = result.scalar_one_or_none()
    
    await callback.message.answer(
        f"✅ Enlace generado exitosamente para el plan '{plan.name}':\n\n"
        f"{link}\n\n"
        f"Este enlace se puede utilizar una sola vez para activar una suscripción."
    )
    
    await state.clear()

# Gestión de usuarios VIP manualmente
@router.callback_query(F.data == "manage_vip_users")
async def manage_vip_users(callback: CallbackQuery):
    await callback.answer()
    # Aquí implementarías la lógica para gestionar usuarios VIP manualmente
    # Por ejemplo, mostrar una lista de usuarios, agregar o quitar usuarios, etc.
    await callback.message.answer(
        "Funcionalidad de gestión de usuarios VIP en desarrollo."
    )

# Configuración de canales
@router.callback_query(F.data == "channel_config")
async def channel_config(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Configuración de canales",
        reply_markup=get_channel_config_keyboard()
    )

# Función para gestionar la configuración de canales
@router.callback_query(F.data.startswith("channel_"))
async def process_channel_config(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    action = callback.data.split("_")[1]
    
    if action == "free":
        current_channel = FREE_CHANNEL_ID
        channel_type = "gratuito"
    elif action == "vip":
        current_channel = VIP_CHANNEL_ID
        channel_type = "VIP"
    else:
        await callback.message.answer("Acción no válida.")
        return
    
    try:
        # Obtener información del canal
        chat = await bot.get_chat(current_channel)
        
        # Intentar crear un enlace de invitación para verificar permisos
        invite_link = await ChannelService.create_channel_invite(bot, current_channel)
        
        if invite_link:
            await callback.message.answer(
                f"✅ Canal {channel_type} configurado correctamente.\n\n"
                f"📢 Nombre: {chat.title}\n"
                f"🔗 Enlace de invitación: {invite_link}"
            )
        else:
            await callback.message.answer(
                f"⚠️ El bot está conectado al canal {channel_type}, pero no tiene permisos para crear enlaces de invitación."
            )
    except Exception as e:
        await callback.message.answer(
            f"❌ Error al configurar el canal {channel_type}: {str(e)}\n\n"
            f"Asegúrate de que el bot sea administrador del canal y tenga los permisos necesarios."
        )

# Envío de mensajes a canales
@router.callback_query(F.data == "send_message", StateFilter(None))
async def send_message_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    # Crear teclado para seleccionar canal
    keyboard = [
        [("Canal Gratuito", "channel_free")],
        [("Canal VIP", "channel_vip")],
        [("Cancelar", "cancel")]
    ]
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    
    for row in keyboard:
        for text, data in row:
            kb.button(text=text, callback_data=data)
        kb.adjust(1)
    
    await callback.message.answer(
        "Selecciona el canal al que quieres enviar el mensaje:",
        reply_markup=kb.as_markup()
    )
    await state.set_state(SendMessage.selecting_channel)

@router.callback_query(StateFilter(SendMessage.selecting_channel))
async def process_channel_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    if callback.data == "cancel":
        await state.clear()
        await callback.message.answer("Envío de mensaje cancelado.")
        return
    
    channel_type = callback.data.split("_")[1]
    
    if channel_type == "free":
        channel_id = FREE_CHANNEL_ID
        channel_name = "Canal Gratuito"
    elif channel_type == "vip":
        channel_id = VIP_CHANNEL_ID
        channel_name = "Canal VIP"
    else:
        await callback.message.answer("Canal no válido.")
        await state.clear()
        return
    
    await state.update_data(channel_id=channel_id, channel_name=channel_name)
    
    await callback.message.answer(
        f"Has seleccionado enviar un mensaje al {channel_name}.\n\n"
        f"Por favor, escribe el texto del mensaje:"
    )
    await state.set_state(SendMessage.entering_text)

@router.message(StateFilter(SendMessage.entering_text))
async def process_message_text(message: Message, state: FSMContext):
    text = message.text.strip()
    
    if not text:
        await message.answer("El mensaje no puede estar vacío. Intenta nuevamente:")
        return
    
    await state.update_data(text=text)
    
    # Preguntar si quiere incluir media
    keyboard = [
        [("Texto solamente", "media_none")],
        [("Incluir imagen", "media_photo")],
        [("Incluir video", "media_video")],
        [("Incluir documento", "media_document")],
        [("Cancelar", "cancel")]
    ]
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    
    for row in keyboard:
        for text, data in row:
            kb.button(text=text, callback_data=data)
        kb.adjust(1)
    
    await message.answer(
        "¿Deseas incluir algún archivo multimedia?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(SendMessage.selecting_media)

@router.callback_query(StateFilter(SendMessage.selecting_media))
async def process_media_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    if callback.data == "cancel":
        await state.clear()
        await callback.message.answer("Envío de mensaje cancelado.")
        return
    
    media_type = callback.data.split("_")[1]
    await state.update_data(media_type=media_type)
    
    if media_type == "none":
        # Preguntar si quiere proteger el contenido
        await prompt_content_protection(callback.message, state)
    else:
        # Solicitar el archivo multimedia
        media_names = {
            "photo": "una imagen",
            "video": "un video",
            "document": "un documento"
        }
        
        await callback.message.answer(f"Por favor, envía {media_names[media_type]}:")
        await state.set_state(SendMessage.selecting_protection)

# Función para procesar archivos de imagen, video o documento
@router.message(StateFilter(SendMessage.selecting_protection), F.photo | F.video | F.document)
async def process_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_type = data.get("media_type")
    
    if media_type == "photo" and message.photo:
        # Tomar la última foto (mejor calidad)
        file_id = message.photo[-1].file_id
    elif media_type == "video" and message.video:
        file_id = message.video.file_id
    elif media_type == "document" and message.document:
        file_id = message.document.file_id
    else:
        await message.answer(f"Por favor, envía un archivo de tipo {media_type}:")
        return
    
    await state.update_data(media_id=file_id)
    
    # Preguntar si quiere proteger el contenido
    await prompt_content_protection(message, state)

async def prompt_content_protection(message, state: FSMContext):
    keyboard = [
        [("Sí, proteger", "protect_yes")],
        [("No, permitir reenvío", "protect_no")],
        [("Cancelar", "cancel")]
    ]
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    
    for row in keyboard:
        for text, data in row:
            kb.button(text=text, callback_data=data)
        kb.adjust(1)
    
    await message.answer(
        "¿Deseas proteger este contenido para evitar que sea reenviado?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(SendMessage.selecting_buttons)

@router.callback_query(StateFilter(SendMessage.selecting_buttons))
async def process_protection_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    if callback.data == "cancel":
        await state.clear()
        await callback.message.answer("Envío de mensaje cancelado.")
        return
    
    is_protected = callback.data == "protect_yes"
    await state.update_data(is_protected=is_protected)
    
    # Preguntar si quiere agregar botones
    keyboard = [
        [("Sí, agregar botones", "buttons_yes")],
        [("No, sin botones", "buttons_no")],
        [("Cancelar", "cancel")]
    ]
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    
    for row in keyboard:
        for text, data in row:
            kb.button(text=text, callback_data=data)
        kb.adjust(1)
    
    await callback.message.answer(
        "¿Deseas agregar botones interactivos al mensaje?",
        reply_markup=kb.as_markup()
    )
    await state.set_state(SendMessage.scheduling)

@router.callback_query(StateFilter(SendMessage.scheduling))
async def process_buttons_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    
    if callback.data == "cancel":
        await state.clear()
        await callback.message.answer("Envío de mensaje cancelado.")
        return
    
    has_buttons = callback.data == "buttons_yes"
    await state.update_data(has_buttons=has_buttons)
    
    if has_buttons:
        # Aquí implementarías la lógica para configurar botones
        # Por simplicidad, en este ejemplo vamos a omitir esa parte
        await callback.message.answer(
            "La configuración de botones no está implementada en este ejemplo. Continuando sin botones."
        )
    
    # Preguntar si quiere programar el mensaje
    keyboard = [
        [("Enviar ahora", "schedule_now")],
        [("Programar para más tarde", "schedule_later")],
        [("Cancelar", "cancel")]
    ]
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    
    for row in keyboard:
        for text, data in row:
            kb.button(text=text, callback_data=data)
        kb.adjust(1)
    
    await callback.message.answer(
        "¿Cuándo quieres enviar este mensaje?",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data.startswith("schedule_"), StateFilter(SendMessage.scheduling))
async def process_scheduling(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    
    if callback.data == "cancel":
        await state.clear()
        await callback.message.answer("Envío de mensaje cancelado.")
        return
    
    schedule_type = callback.data.split("_")[1]
    data = await state.get_data()
    
    if schedule_type == "later":
        # Aquí implementarías la lógica para programar el mensaje
        # Por simplicidad, en este ejemplo vamos a omitir esa parte
        await callback.message.answer(
            "La programación de mensajes no está implementada en este ejemplo. Enviando mensaje ahora."
        )
        schedule_type = "now"
    
    if schedule_type == "now":
        # Enviar mensaje inmediatamente
        channel_id = data.get("channel_id")
        text = data.get("text")
        media_type = data.get("media_type")
        media_id = data.get("media_id")
        is_protected = data.get("is_protected", False)
        
        try:
            if media_type == "none" or not media_id:
                await bot.send_message(
                    chat_id=channel_id,
                    text=text,
                    protect_content=is_protected
                )
            elif media_type == "photo":
                await bot.send_photo(
                    chat_id=channel_id,
                    photo=media_id,
                    caption=text,
                    protect_content=is_protected
                )
            elif media_type == "video":
                await bot.send_video(
                    chat_id=channel_id,
                    video=media_id,
                    caption=text,
                    protect_content=is_protected
                )
            elif media_type == "document":
                await bot.send_document(
                    chat_id=channel_id,
                    document=media_id,
                    caption=text,
                    protect_content=is_protected
                )
            
            await callback.message.answer("✅ Mensaje enviado exitosamente.")
        except Exception as e:
            await callback.message.answer(f"❌ Error al enviar mensaje: {str(e)}")
    
    await state.clear()