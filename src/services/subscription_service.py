"""
Subscription management service
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from src.repositories.user_repository import UserRepository
from src.models.user import SubscriptionStatus

logger = logging.getLogger(__name__)

# Plan configurations
PLAN_CONFIGS = {
    "free": {
        "name": "無料プラン",
        "ai_calls_limit": 10,  # Monthly limit
        "use_ai_agent": False,  # Default to pattern matching
        "price": 0
    },
    "basic": {
        "name": "ベーシックプラン",
        "ai_calls_limit": 100,
        "use_ai_agent": True,
        "price": 500  # 500円/月
    },
    "premium": {
        "name": "プレミアムプラン",
        "ai_calls_limit": -1,  # Unlimited
        "use_ai_agent": True,
        "price": 1500  # 1500円/月
    }
}


class SubscriptionService:
    """Service for managing user subscriptions"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    async def check_ai_availability(self, line_user_id: str) -> tuple[bool, str]:
        """
        Check if user can use AI agent
        
        Args:
            line_user_id: LINE user ID
            
        Returns:
            Tuple of (can_use_ai, reason_message)
        """
        try:
            user = await self.user_repo.get_user(line_user_id)
            if not user:
                return False, "ユーザー情報が見つかりません"
            
            subscription = user.get('subscription', {})
            plan = subscription.get('plan', 'free')
            
            # Check if plan allows AI
            plan_config = PLAN_CONFIGS.get(plan, PLAN_CONFIGS['free'])
            
            # Premium users always have access
            if plan == 'premium':
                return True, ""
            
            # Check monthly limit for other plans
            ai_calls_used = subscription.get('ai_calls_used', 0)
            ai_calls_limit = plan_config['ai_calls_limit']
            
            # Reset monthly counter if needed
            last_reset = subscription.get('last_reset_at')
            if last_reset:
                last_reset_date = datetime.fromisoformat(last_reset)
                if datetime.now() - last_reset_date > timedelta(days=30):
                    # Reset counter
                    await self._reset_monthly_counter(line_user_id)
                    ai_calls_used = 0
            
            # Check limit
            if ai_calls_limit > 0 and ai_calls_used >= ai_calls_limit:
                return False, (
                    f"今月のAI利用回数上限（{ai_calls_limit}回）に達しました。\n"
                    f"プランをアップグレードするか、来月までお待ちください。"
                )
            
            # Check if user has explicitly enabled AI
            preferences = user.get('preferences', {})
            if not preferences.get('use_ai_agent', False):
                return False, (
                    "AIモードが無効になっています。\n"
                    "設定から有効にしてください。"
                )
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking AI availability: {e}")
            return False, "エラーが発生しました"
    
    async def increment_ai_usage(self, line_user_id: str) -> bool:
        """
        Increment AI usage counter
        
        Args:
            line_user_id: LINE user ID
            
        Returns:
            True if successful
        """
        try:
            user = await self.user_repo.get_user(line_user_id)
            if not user:
                return False
            
            subscription = user.get('subscription', {})
            ai_calls_used = subscription.get('ai_calls_used', 0)
            
            # Update counter
            subscription['ai_calls_used'] = ai_calls_used + 1
            
            return await self.user_repo.update(line_user_id, {
                'subscription': subscription
            })
            
        except Exception as e:
            logger.error(f"Error incrementing AI usage: {e}")
            return False
    
    async def _reset_monthly_counter(self, line_user_id: str) -> bool:
        """Reset monthly AI usage counter"""
        try:
            user = await self.user_repo.get_user(line_user_id)
            if not user:
                return False
            
            subscription = user.get('subscription', {})
            subscription['ai_calls_used'] = 0
            subscription['last_reset_at'] = datetime.now().isoformat()
            
            return await self.user_repo.update(line_user_id, {
                'subscription': subscription
            })
            
        except Exception as e:
            logger.error(f"Error resetting counter: {e}")
            return False
    
    async def upgrade_plan(self, line_user_id: str, new_plan: str) -> Dict[str, Any]:
        """
        Upgrade user's subscription plan
        
        Args:
            line_user_id: LINE user ID
            new_plan: New plan name
            
        Returns:
            Result dictionary
        """
        try:
            if new_plan not in PLAN_CONFIGS:
                return {
                    'success': False,
                    'message': '無効なプランです'
                }
            
            user = await self.user_repo.get_user(line_user_id)
            if not user:
                return {
                    'success': False,
                    'message': 'ユーザー情報が見つかりません'
                }
            
            # Update subscription
            subscription = user.get('subscription', {})
            old_plan = subscription.get('plan', 'free')
            
            subscription['plan'] = new_plan
            subscription['is_active'] = True
            subscription['expires_at'] = (datetime.now() + timedelta(days=30)).isoformat()
            
            # Enable AI for paid plans
            preferences = user.get('preferences', {})
            if new_plan in ['basic', 'premium']:
                preferences['use_ai_agent'] = True
            
            # Update user
            success = await self.user_repo.update(line_user_id, {
                'subscription': subscription,
                'preferences': preferences
            })
            
            if success:
                plan_config = PLAN_CONFIGS[new_plan]
                return {
                    'success': True,
                    'message': (
                        f"{plan_config['name']}にアップグレードしました！\n"
                        f"{'AIモード' if plan_config['use_ai_agent'] else 'パターン認識モード'}が利用可能です。"
                    ),
                    'old_plan': old_plan,
                    'new_plan': new_plan
                }
            
            return {
                'success': False,
                'message': 'プランの更新に失敗しました'
            }
            
        except Exception as e:
            logger.error(f"Error upgrading plan: {e}")
            return {
                'success': False,
                'message': 'エラーが発生しました'
            }
    
    async def get_subscription_info(self, line_user_id: str) -> Dict[str, Any]:
        """Get user's subscription information"""
        try:
            user = await self.user_repo.get_user(line_user_id)
            if not user:
                return None
            
            subscription = user.get('subscription', {})
            plan = subscription.get('plan', 'free')
            plan_config = PLAN_CONFIGS.get(plan, PLAN_CONFIGS['free'])
            
            # Calculate remaining AI calls
            ai_calls_used = subscription.get('ai_calls_used', 0)
            ai_calls_limit = plan_config['ai_calls_limit']
            ai_calls_remaining = (
                '無制限' if ai_calls_limit == -1 
                else max(0, ai_calls_limit - ai_calls_used)
            )
            
            return {
                'plan': plan,
                'plan_name': plan_config['name'],
                'is_active': subscription.get('is_active', True),
                'expires_at': subscription.get('expires_at'),
                'ai_calls_used': ai_calls_used,
                'ai_calls_limit': '無制限' if ai_calls_limit == -1 else ai_calls_limit,
                'ai_calls_remaining': ai_calls_remaining,
                'price': plan_config['price'],
                'features': {
                    'ai_agent': plan_config['use_ai_agent'],
                    'pattern_matching': True  # Always available
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription info: {e}")
            return None