# telegram_subscription_bot/services/channel_service.py
from sqlalchemy import select, update
from database.db import get_session
from database.models import User
from aiogram import Bot
from config import FREE_CHANNEL_ID, VIP_CHANNEL_ID

class ChannelService:
    @staticmethod
    async def check_user_in_channel(bot: Bot, user_id: int, channel_id: str):
        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            return chat_member.status not in ['left', 'kicked', 'banned']
        except Exception as e:
            print(f"Error checking channel membership: {e}")
            return False
    
    @staticmethod
    async def update_free_channel_status(user_id: int, is_in_channel: bool):
        async with get_session() as session:
            user_result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = user_result.scalar_one_or_none()
            
            if user:
                user.is_in_free_channel = is_in_channel
                await session.commit()
                return True
            return False
    
    @staticmethod
    async def create_channel_invite(bot: Bot, channel_id: str):
        try:
            # Crear enlace de invitación para el canal
            invite_link = await bot.create_chat_invite_link(
                chat_id=channel_id,
                creates_join_request=False,
                name="Bot Invitation"
            )
            return invite_link.invite_link
        except Exception as e:
            print(f"Error creating channel invite: {e}")
            return None
    
    @staticmethod
    async def kick_user_from_channel(bot: Bot, user_id: int, channel_id: str):
        try:
            await bot.ban_chat_member(chat_id=channel_id, user_id=user_id)
            # Inmediatamente desbanear para que pueda volver a unirse en el futuro
            await bot.unban_chat_member(chat_id=channel_id, user_id=user_id, only_if_banned=True)
            return True
        except Exception as e:
            print(f"Error kicking user from channel: {e}")
            return False
    
    @staticmethod
    async def get_free_channel_users(bot: Bot):
        try:
            async with get_session() as session:
                query = select(User).where(User.is_in_free_channel == True)
                result = await session.execute(query)
                users = result.scalars().all()
                
                # Verificar realmente quiénes siguen en el canal
                verified_users = []
                for user in users:
                    is_in_channel = await ChannelService.check_user_in_channel(bot, user.telegram_id, FREE_CHANNEL_ID)
                    if not is_in_channel:
                        user.is_in_free_channel = False
                    else:
                        verified_users.append(user)
                
                await session.commit()
                return verified_users
        except Exception as e:
            print(f"Error getting free channel users: {e}")
            return []