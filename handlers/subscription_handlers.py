# telegram_subscription_bot/handlers/subscription_handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from services.subscription_service import SubscriptionService
from services.channel_service import ChannelService
from config import VIP_CHANNEL_ID

router = Router()

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    await callback.answer()
    
    from keyboards.admin_keyboards import get_admin_main_menu
    await callback.message.edit_text(
        "Panel de Administración",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data == "statistics")
async def show_statistics(callback: CallbackQuery):
    await callback.answer()
    
    # Aquí implementarías la lógica para mostrar estadísticas
    # Por ejemplo, número de usuarios, suscripciones activas, etc.
    
    await callback.message.answer(
        "📊 Estadísticas\n\n"
        "Funcionalidad de estadísticas en desarrollo."
    )
