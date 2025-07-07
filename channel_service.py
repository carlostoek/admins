#services/channel_service.py
from sqlalchemy import select, update
from database.db import get_session
from database.models import User
from aiogram import Bot
from config import FREE_CHANNEL_ID, VIP_CHANNEL_ID

class ChannelService:
    @staticmethod
    async def check_user_in_channel(bot: Bot, user_id: int, channel