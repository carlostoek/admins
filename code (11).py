# telegram_subscription_bot/handlers/user_handlers.py
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import get_session
from database.models import User
from services.token_service import TokenService
from services.subscription_service import SubscriptionService
from services.channel_service import ChannelService
from keyboards.user_keyboards import get_user_main_menu
from config import FREE_CHANNEL_ID, VIP_CHANNEL_ID, FREE_CHANNEL_OPEN_ACCESS

router = Router()

@router.message(CommandStart())
async def start_command(message: Message, bot: Bot):
    # Comprobar si hay un token en el comando start
    args = message.text.split()
    token_value = args[1] if len(args) > 1 else None
    
    # Mensaje de bienvenida básico
    user_name = message.from_user.first_name
    welcome_message = f"👋 ¡Hola, {user_name}! Bienvenido al Bot de Gestión de Suscripciones."
    
    # Verificar el token si existe
    if token_value:
        # Validar token
        token = await TokenService.validate_token(token_value)
        
        if token:
            # Token válido, activar suscripción
            subscription = await SubscriptionService.subscribe_user(message.from_user.id, token.plan_id)
            
            if subscription:
                # Marcar token como usado
                await TokenService.use_token(token_value, message.from_user.id)
                
                # Generar invitación al canal VIP
                invite_link = await ChannelService.create_channel_invite(bot, VIP_CHANNEL_ID)
                
                if invite_link:
                    await message.answer(
                        f"{welcome_message}\n\n"
                        f"✅ ¡Tu suscripción VIP ha sido activada exitosamente!\n\n"
                        f"Haz clic en el siguiente enlace para unirte al canal VIP:\n"
                        f"{invite_link}"
                    )
                else:
                    await message.answer(
                        f"{welcome_message}\n\n"
                        f"✅ ¡Tu suscripción VIP ha sido activada exitosamente!\n\n"
                        f"❌ Sin embargo, hubo un problema al generar el enlace de invitación. Por favor, contacta al administrador."
                    )
            else:
                await message.answer(
                    f"{welcome_message}\n\n"
                    f"❌ Hubo un problema al activar tu suscripción. Por favor, contacta al administrador."
                )
        else:
            # Token inválido o ya usado
            await message.answer(
                f"{welcome_message}\n\n"
                f"❌ El enlace que utilizaste no es válido o ya ha sido utilizado."
            )
    else:
        # No hay token, simplemente dar la bienvenida
        # Verificar si el usuario está en el canal gratuito
        is_in_free_channel = await ChannelService.check_user_in_channel(bot, message.from_user.id, FREE_CHANNEL_ID)
        
        # Actualizar estado en la base de datos
        await ChannelService.update_free_channel_status(message.from_user.id, is_in_free_channel)
        
        if is_in_free_channel or FREE_CHANNEL_OPEN_ACCESS:
            # Si ya está en el canal o el acceso es libre, mostrar menú principal
            await message.answer(
                f"{welcome_message}\n\n"
                f"Usa los botones a continuación para navegar:",
                reply_markup=get_user_main_menu()
            )
        else:
            # Si no está en el canal y se requiere estar en él, enviar invitación
            invite_link = await ChannelService.create_channel_invite(bot, FREE_CHANNEL_ID)
            
            if invite_link:
                await message.answer(
                    f"{welcome_message}\n\n"
                    f"Para continuar, por favor únete a nuestro canal gratuito:\n"
                    f"{invite_link}\n\n"
                    f"Una vez que te hayas unido, pulsa /start nuevamente."
                )
            else:
                await message.answer(
                    f"{welcome_message}\n\n"
                    f"Parece que hay un problema con el enlace de invitación. Por favor, contacta al administrador."
                )

@router.message(Command("menu"))
async def menu_command(message: Message, bot: Bot):
    # Verificar si el usuario está en el canal gratuito
    is_in_free_channel = await ChannelService.check_user_in_channel(bot, message.from_user.id, FREE_CHANNEL_ID)
    
    # Actualizar estado en la base de datos
    await ChannelService.update_free_channel_status(message.from_user.id, is_in_free_channel)
    
    if is_in_free_channel or FREE_CHANNEL_OPEN_ACCESS:
        # Mostrar menú principal
        await message.answer(
            "🔍 Menú Principal",
            reply_markup=get_user_main_menu()
        )
    else:
        # Si no está en el canal y se requiere estar en él, enviar invitación
        invite_link = await ChannelService.create_channel_invite(bot, FREE_CHANNEL_ID)
        
        if invite_link:
            await message.answer(
                "Para acceder al menú, primero debes unirte a nuestro canal gratuito:\n"
                f"{invite_link}\n\n"
                f"Una vez que te hayas unido, pulsa /menu nuevamente."
            )

@router.callback_query(F.data == "subscription_status")
async def subscription_status(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    
    # Verificar estado de suscripción
    subscription = await SubscriptionService.get_active_subscription(callback.from_user.id)
    
    if subscription:
        # Tiene suscripción activa
        async with get_session() as session:
            # Obtener detalles del plan
            from database.models import SubscriptionPlan
            result = await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id))
            plan = result.scalar_one_or_none()
            
            if subscription.end_date:
                # Suscripción con fecha de expiración
                import datetime
                days_left = (subscription.end_date - datetime.datetime.utcnow()).days
                
                await callback.message.answer(
                    f"🔰 Estado de tu Suscripción VIP\n\n"
                    f"Plan: {plan.name}\n"
                    f"Estado: Activa ✅\n"
                    f"Días restantes: {days_left if days_left > 0 else 'Menos de un día'}\n"
                    f"Fecha de expiración: {subscription.end_date.strftime('%d/%m/%Y')}"
                )
            else:
                # Suscripción permanente
                await callback.message.answer(
                    f"🔰 Estado de tu Suscripción VIP\n\n"
                    f"Plan: {plan.name}\n"
                    f"Estado: Activa ✅\n"
                    f"Duración: Permanente ♾️"
                )
    else:
        # No tiene suscripción activa
        await callback.message.answer(
            "📛 No tienes una suscripción VIP activa.\n\n"
            "Para obtener acceso al contenido VIP, contacta con el administrador."
        )

@router.callback_query(F.data == "help")
async def help_command(callback: CallbackQuery):
    await callback.answer()
    
    await callback.message.answer(
        "ℹ️ Ayuda del Bot\n\n"
        "Este bot te permite acceder a diferentes canales según tu nivel de suscripción.\n\n"
        "Comandos disponibles:\n"
        "/start - Iniciar el bot\n"
        "/menu - Mostrar el menú principal\n\n"
        "Si tienes problemas o preguntas, contacta al administrador."
    )