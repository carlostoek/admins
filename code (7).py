# telegram_subscription_bot/services/subscription_service.py
import datetime
from sqlalchemy import select, update
from database.db import get_session
from database.models import User, Subscription, SubscriptionPlan

class SubscriptionService:
    @staticmethod
    async def create_subscription_plan(name, duration_days, price, is_permanent=False):
        async with get_session() as session:
            plan = SubscriptionPlan(
                name=name,
                duration_days=duration_days,
                price=price,
                is_permanent=is_permanent
            )
            session.add(plan)
            await session.commit()
            return plan
    
    @staticmethod
    async def get_subscription_plans():
        async with get_session() as session:
            result = await session.execute(select(SubscriptionPlan))
            return result.scalars().all()
    
    @staticmethod
    async def subscribe_user(user_id, plan_id):
        async with get_session() as session:
            # Obtener plan
            plan_result = await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
            plan = plan_result.scalar_one_or_none()
            
            if not plan:
                return None
            
            # Obtener usuario
            user_result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = user_result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Calcular fecha de finalización
            end_date = None if plan.is_permanent else datetime.datetime.utcnow() + datetime.timedelta(days=plan.duration_days)
            
            # Crear suscripción
            subscription = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                start_date=datetime.datetime.utcnow(),
                end_date=end_date,
                is_active=True
            )
            
            session.add(subscription)
            await session.commit()
            return subscription
    
    @staticmethod
    async def get_active_subscription(user_id):
        async with get_session() as session:
            # Obtener usuario
            user_result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = user_result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Obtener suscripción activa
            now = datetime.datetime.utcnow()
            subscription_query = select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.is_active == True,
                (Subscription.end_date == None) | (Subscription.end_date > now)
            )
            
            subscription_result = await session.execute(subscription_query)
            return subscription_result.scalar_one_or_none()
    
    @staticmethod
    async def get_expiring_subscriptions(days=1):
        async with get_session() as session:
            now = datetime.datetime.utcnow()
            expiry_date = now + datetime.timedelta(days=days)
            
            query = select(Subscription, User).join(User).where(
                Subscription.is_active == True,
                Subscription.end_date != None,
                Subscription.end_date <= expiry_date,
                Subscription.end_date > now
            )
            
            result = await session.execute(query)
            return result.all()
    
    @staticmethod
    async def deactivate_expired_subscriptions():
        async with get_session() as session:
            now = datetime.datetime.utcnow()
            
            stmt = update(Subscription).where(
                Subscription.is_active == True,
                Subscription.end_date != None,
                Subscription.end_date <= now
            ).values(is_active=False)
            
            await session.execute(stmt)
            await session.commit()