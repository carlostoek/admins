# telegram_subscription_bot/services/token_service.py
import uuid
from sqlalchemy import select
from database.db import get_session
from database.models import Token, SubscriptionPlan, User

class TokenService:
    @staticmethod
    async def generate_token(plan_id):
        async with get_session() as session:
            # Verificar que el plan existe
            plan_result = await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
            plan = plan_result.scalar_one_or_none()
            
            if not plan:
                return None
            
            # Generar token único
            token_value = str(uuid.uuid4())
            
            # Crear registro de token
            token = Token(
                token=token_value,
                plan_id=plan_id,
                is_used=False
            )
            
            session.add(token)
            await session.commit()
            return token
    
    @staticmethod
    async def validate_token(token_value):
        async with get_session() as session:
            token_result = await session.execute(
                select(Token).where(
                    Token.token == token_value,
                    Token.is_used == False
                )
            )
            token = token_result.scalar_one_or_none()
            
            if not token:
                return None
            
            return token
    
    @staticmethod
    async def use_token(token_value, user_id):
        async with get_session() as session:
            # Obtener token
            token_result = await session.execute(
                select(Token).where(
                    Token.token == token_value,
                    Token.is_used == False
                )
            )
            token = token_result.scalar_one_or_none()
            
            if not token:
                return None
            
            # Marcar token como usado
            token.is_used = True
            token.used_by = user_id
            
            await session.commit()
            return token