# telegram_subscription_bot/middlewares/access_middleware.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from database.db import get_session
from database.models import User
from config import ADMIN_IDS

class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Extraer user_id del evento
        if isinstance(event, Message):
            user_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name
            last_name = event.from_user.last_name
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name
            last_name = event.from_user.last_name
        else:
            # Tipo de evento no soportado
            return await handler(event, data)
        
        # Registrar o actualizar usuario en la base de datos
        async with get_session() as session:
            result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                # Crear nuevo usuario
                user = User(
                    telegram_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=user_id in ADMIN_IDS
                )
                session.add(user)
            else:
                # Actualizar datos del usuario
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.is_admin = user_id in ADMIN_IDS
            
            await session.commit()
        
        # Continuar con el manejador
        return await handler(event, data)