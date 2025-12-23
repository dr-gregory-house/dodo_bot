import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

logger = logging.getLogger(__name__)

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is a Telegram Chat Admin or Creator."""
    if update.effective_chat.type == 'private':
        return True
        
    try:
        member = await update.effective_chat.get_member(update.effective_user.id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def get_user_role(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """
    Get user role based on surname.
    Returns role name if manager/admin, else None.
    """
    surname = context.user_data.get('surname')
    
    if not surname:
        try:
            import json
            import os
            if os.path.exists('data/users.json'):
                with open('data/users.json', 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    surname = users.get(str(user_id))
                    if surname:
                        context.user_data['surname'] = surname
        except:
            pass
            
    if not surname:
        return None
        
    surname_lower = surname.lower()
    
    # Hardcoded authorized managers
    if 'мишра' in surname_lower:
        return "Мишра"
    elif 'ахмитенко' in surname_lower:
        return "Менеджер"
    elif 'булатова' in surname_lower:
        return "Менеджер"
        
    return None

async def check_authorization(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """
    Legacy check for ratings.py compatibility.
    Returns (is_authorized, role)
    """
    # This function mimics the old behavior for ratings.py
    # It only checks the "Manager" role logic, not Telegram Admin status
    # because ratings might be restricted to specific people even if they are chat admins?
    # The original code only checked surnames.
    
    role = await get_user_role(user_id, context)
    if role:
        return True, role
    return False, None
