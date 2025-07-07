# telegram_subscription_bot/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db
from handlers import admin_handlers, user_handlers, subscription_handlers, channel_handlers
from middlewares.access_middleware import AccessMiddleware
from services.scheduler_service import SchedulerService

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    # Inicializar la base de datos
    await init_db()
    
    # Inicializar el bot y el dispatcher
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Registrar middlewares
    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())
    
    # Incluir routers
    dp.include_router(admin_handlers.router)
    dp.include_router(subscription_handlers.router)
    dp.include_router(channel_handlers.router)
    dp.include_router(user_handlers.router)  # Siempre al final para capturar mensajes no manejados
    
    # Inicializar el servicio de programación
    scheduler_service = SchedulerService(bot)
    await scheduler_service.start()
    
    # Eliminar webhook por si acaso
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Iniciar polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await scheduler_service.stop()

if __name__ == "__main__":
    asyncio.run(main())